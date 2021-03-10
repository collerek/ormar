# Encryption

`ormar` provides you with a way to encrypt a field in the database only.
Provided encryption backends allow for both one-way encryption (`HASH` backend) as
well as both-way encryption/decryption (`FERNET` backend).

!!!warning
    Note that in order for encryption to work you need to install optional `cryptography` package.

    You can do it manually `pip install cryptography` or with ormar by `pip install ormar[crypto]`

!!!warning
    Note that adding `encrypt_backend` changes the database column type to `TEXT`, 
    which needs to be reflected in db either by migration (`alembic`) or manual change

## Defining a field encryption

To encrypt a field you need to pass at minimum `encrypt_secret` and `encrypt_backend` parameters.

```python hl_lines="7-8"
class Filter(ormar.Model):
    class Meta(BaseMeta):
        tablename = "filters"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, 
                             encrypt_secret="secret123", 
                             encrypt_backend=ormar.EncryptBackends.FERNET)
```

!!!warning
    You can encrypt all `Field` types apart from `primary_key` column and relation 
    columns (`ForeignKey` and `ManyToMany`). Check backends details for more information.

## Available backends

### HASH

HASH is a one-way hash (like for password), never decrypted on retrieval

To set it up pass appropriate backend value.

```python
... # rest of model definition
password: str = ormar.String(max_length=128,
                         encrypt_secret="secret123", 
                         encrypt_backend=ormar.EncryptBackends.HASH)
```

Note that since this backend never decrypt the stored value it's only applicable for
`String` fields. Used hash is a `sha512` hash, so the field length has to be >=128.

!!!warning
    Note that in `HASH` backend you can filter by full value but filters like `contain` will not work as comparison is make on encrypted values

!!!note 
    Note that provided `encrypt_secret` is first hashed itself and used as salt, so in order to
    compare to stored string you need to recreate this steps.

```python
class Hash(ormar.Model):
    class Meta(BaseMeta):
        tablename = "hashes"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=128,
                             encrypt_secret="udxc32",
                             encrypt_backend=ormar.EncryptBackends.HASH)


await Hash(name='test1').save()

# note the steps to recreate the stored value
# you can use also cryptography package instead of hashlib
secret = hashlib.sha256("udxc32".encode()).digest()
secret = base64.urlsafe_b64encode(secret)
hashed_test1 = hashlib.sha512(secret + 'test1'.encode()).hexdigest()

# full value comparison works
hash1 = await Hash.objects.get(name='test1')
assert hash1.name == hashed_test1

# but partial comparison does not (hashed strings are compared)
with pytest.raises(NoMatch):
    await Filter.objects.get(name__icontains='test')
```

### FERNET

FERNET is a two-way encrypt/decrypt backend

To set it up pass appropriate backend value.

```python
... # rest of model definition
year: int = ormar.Integer(encrypt_secret="secret123", 
                          encrypt_backend=ormar.EncryptBackends.FERNET)
```

Value is encrypted on way to database end decrypted on way out. Can be used on all types,
as the returned value is parsed to corresponding python type.

!!!warning
    Note that in `FERNET` backend you loose `filtering` possibility altogether as part of the encrypted value is a timestamp

```python
class Filter(ormar.Model):
    class Meta(BaseMeta):
        tablename = "filters"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, 
                             encrypt_secret="asd123", 
                             encrypt_backend=ormar.EncryptBackends.FERNET)

await Filter(name='test1').save()
await Filter(name='test1').save()

# values are properly encrypted and later decrypted
filters = await Filter.objects.all()
assert filters[0].name == filters[1].name == 'test1'

# but you cannot filter at all since part of the fernet hash is a timestamp
# which means that even if you encrypt the same string 2 times it will be different
with pytest.raises(NoMatch):
    await Filter.objects.get(name='test1')
```

## Custom Backends

If you wish to support other type of encryption (i.e. AES) you can provide your own `EncryptionBackend`.

To setup a backend all you need to do is subclass `ormar.fields.EncryptBackend` class and provide required backend.

Sample dummy backend (that does nothing) can look like following:

```python
class DummyBackend(ormar.fields.EncryptBackend):
    def _initialize_backend(self, secret_key: bytes) -> None:
        pass

    def encrypt(self, value: Any) -> str:
        return value

    def decrypt(self, value: Any) -> str:
        return value
```

To use this backend set `encrypt_backend` to `CUSTOM` and provide your backend as
argument by `encrypt_custom_backend`.

```python
class Filter(ormar.Model):
    class Meta(BaseMeta):
        tablename = "filters"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, 
                             encrypt_secret="secret123", 
                             encrypt_backend=ormar.EncryptBackends.CUSTOM,
                             encrypt_custom_backend=DummyBackend
                             )
```