"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None


    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        print(f"Количество клиентов: {len(self.server.clients)}")
        print(f"Логин: {self.login}")
        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                # self.login = decoded.replace("login:", "").replace("\r\n", "")
                login = decoded.replace("login:", "").replace("\r\n", "")
                print(f"Логин нового пользователя: {login}")
                i = 0
                while i < len(self.server.clients):
                    if self.server.clients[i].login == login:
                        print(f"Данный логин продублировался: {login}")
                        self.transport.write(f"Логин {login} занят, попробуйте другой".encode())
                        self.transport.close()
                        break
                    i = i + 1
                    print(f"Цикл завершился, число повторений: {i}")
                self.login = login
                self.transport.write(
                    f"Привет, {self.login}!\r\n".encode()
                )
                self.send_history()
        else:
            self.send_message(decoded)

    def send_history(self):
        history_message = self.server.message_history()
        if len(history_message) > 0:
            i = 1
            self.transport.write(f"История сообщений:\r\n".encode())
            for select in reversed(history_message):
                if i <= 10:
                    self.transport.write(f"{select} \r\n".encode())
                i = i + 1
        else:
            return self.transport.write("Исторических сообщений нет".encode())

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        self.server.historyList.append(format_string)
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    historyList: list

    def __init__(self):
        self.clients = []
        self.historyList = []

    def message_history(self):
        return self.historyList

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")