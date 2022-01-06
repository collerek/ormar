# 1. like in example above
await Car.objects.select_related("manufacturer").fields(
    ["id", "name", "manufacturer__name"]
).all()

# 2. to mark a field as required use ellipsis
await Car.objects.select_related("manufacturer").fields(
    {"id": ..., "name": ..., "manufacturer": {"name": ...}}
).all()

# 3. to include whole nested model use ellipsis
await Car.objects.select_related("manufacturer").fields(
    {"id": ..., "name": ..., "manufacturer": ...}
).all()

# 4. to specify fields at last nesting level you can also use set - equivalent to 2. above
await Car.objects.select_related("manufacturer").fields(
    {"id": ..., "name": ..., "manufacturer": {"name"}}
).all()

# 5. of course set can have multiple fields
await Car.objects.select_related("manufacturer").fields(
    {"id": ..., "name": ..., "manufacturer": {"name", "founded"}}
).all()

# 6. you can include all nested fields but it will be equivalent of 3. above which is shorter
await Car.objects.select_related("manufacturer").fields(
    {"id": ..., "name": ..., "manufacturer": {"id", "name", "founded"}}
).all()
