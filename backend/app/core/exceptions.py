class BusinessError(Exception):
    def __init__(self, code, status=422, message='请求参数或范围无效'):
        self.code,self.status,self.message=code,status,message
        super().__init__(code)
