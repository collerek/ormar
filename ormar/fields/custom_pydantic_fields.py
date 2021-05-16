from pydantic import BaseModel


class OrmarBytes(bytes):

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            pass
        return v

    def __get__(self, obj, class_=None):
        return 'test'

    def __set__(self, obj, value):
        obj.__dict__['test'] = value


class ModelA(BaseModel):
    test: OrmarBytes = OrmarBytes()


ModelA.test = OrmarBytes()
aa = ModelA(test=b"aa")
print(aa.__dict__)
print(aa.test)
aa.test = 'aas'
print(aa.test)
