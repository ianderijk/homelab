import logging
import logging.handlers
import pickle
import queue
import socketserver
import struct
import threading
import time
from typing import Any, cast

from data_utils import lh_utils as lh

LISTENING_HOST = "0.0.0.0"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True
)


class LogBufferManager:
    def __init__(self, batch_size: int = 50, flush_interval: float = 30.0) -> None:
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue = queue.Queue()
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._flush_loop, daemon=True)

    def start(self) -> None:
        self._worker_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._worker_thread.join()
        self._flush_remaining()

    def add_record(self, record: logging.LogRecord) -> None:
        self.queue.put(record)

    def _write_batch(self, records: list[logging.LogRecord]) -> None:
        grouped = {}
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        for record in records:
            project = record.name if record.name else "unnamed-project"
            grouped.setdefault(project, []).append(record)

        timestamp = int(time.time())

        for project, log_list in grouped.items():
            formatted_lines = [formatter.format(record) for record in log_list]
            payload = ("\n".join(formatted_lines) + "\n").encode("utf-8")

            filename = f"log_{timestamp}_records"

            try:
                print("sending logs to bucket...")
                lh.send_to_bucket(
                    bucket_name="logs",
                    partition_name=project,
                    bytes_=payload,
                    filename=filename,
                    filetype=".log",
                )
            except Exception as e:  # noqa: BLE001
                logging.error(f"Failed to write batch: {e}")  # noqa: LOG015

    def _flush_loop(self) -> None:
        prev_flush_time = time.time()
        records = []

        while not self._stop_event.is_set():
            try:
                record = self.queue.get(timeout=0.1)
                records.append(record)
            except queue.Empty:
                pass

            now = time.time()
            flush_interval_exceeded = (now - prev_flush_time) >= self.flush_interval
            batch_size_exceeded = len(records) >= self.batch_size
            if records and (flush_interval_exceeded or batch_size_exceeded):
                self._write_batch(records)
                records = []
                prev_flush_time = time.time()

    def _flush_remaining(self) -> None:
        records = []
        while not self.queue.empty():
            try:
                records.append(self.queue.get_nowait())
            except queue.Empty:
                break
        if records:
            self._write_batch(records)


buffer_manager = LogBufferManager()


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break

            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)

            while len(chunk) < slen:
                chunk += self.connection.recv(slen - len(chunk))

            obj = pickle.loads(chunk)
            record = logging.makeLogRecord(obj)

            buffer_manager.add_record(record)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(
        self,
        host: str = LISTENING_HOST,
        port: int = logging.handlers.DEFAULT_TCP_LOGGING_PORT,
        handler=LogRecordStreamHandler,
    ):
        super().__init__((host, port), cast(Any, handler))

    def serve_until_stopped(self):
        try:
            self.serve_forever()
        except (KeyboardInterrupt, SystemExit):
            pass


def main():
    buffer_manager.start()
    tcpserver = LogRecordSocketReceiver()

    try:
        print("Starting log listener")
        tcpserver.serve_until_stopped()
    finally:
        tcpserver.server_close()
        buffer_manager.stop()


if __name__ == "__main__":
    main()
