from proxies.logging_proxy import AsyncLoggingProxy

if __name__ == '__main__':
    proxy: 'AsyncLoggingProxy' = AsyncLoggingProxy()
    try:
        print("Proxy server Started")
        proxy.serve_forever()
    except KeyboardInterrupt:
        proxy.server_close()
        print("Proxy server Disconnected")
