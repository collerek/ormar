# Request

Note that the same (need for additional) applies if you want to pass less fields as request parameters but keep them as required on ormar.Model. This is more rare situation, cause it means that you will get the fields value from somewhere else than request (as you not pass them).

That usually means that you can pass server_default to ormar Fields and that will fill the value in sql, or you can use default ormar Fields parameter and pass either static value or a function (with no args) that will fill this field for you. If you pass default or server_default ormar/pydantic field becomes optional and you can use the same model in request and ormar.

In sample below only last_name is required

```python
def gen_pass():
    choices = string.ascii_letters + string.digits + "!@#$%^&*()".split()
    return "".join(random.choice(choices) for _ in range(20))


class RandomModel(ormar.Model):
    class Meta:
        tablename: str = "users"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    password: str = ormar.String(max_length=255, default=gen_pass)
    first_name: str = ormar.String(max_length=255, default='John')
    # note that in ormar by default if you not provide autoincrement, default or server_default the field is required
    # so nullable=False - you do not need to provide it for each field
    last_name: str = ormar.String(max_length=255)
    created_date: str = ormar.DateTime(server_default=sqlalchemy.func.now())

# that way only last_name is required and you will get "random" password etc.
# so you can still use ormar model in Request param.
@app.post("/random/", response_model=RandomModel)
async def create_user5(user: RandomModel):
    return await user.save()

# you can pass only last_name in payload but still get the data persisted in db
user3 = {
            'last_name': 'Test'
        }
response = client.post("/random/", json=user3)
assert list(response.json().keys()) == ['id', 'password', 'first_name', 'last_name', 'created_date']
```
But if you cannot set default you will need additional pydantic Model.