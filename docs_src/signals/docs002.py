from ormar import pre_update


@pre_update(Album)
async def before_update(sender, instance, **kwargs):
    if instance.play_count > 50 and not instance.is_best_seller:
        instance.is_best_seller = True


# here album.play_count ans is_best_seller get default values
album = await Album.objects.create(name="Venice")
assert not album.is_best_seller
assert album.play_count == 0

album.play_count = 30
# here a trigger is called but play_count is too low
await album.update()
assert not album.is_best_seller

album.play_count = 60
await album.update()
assert album.is_best_seller
