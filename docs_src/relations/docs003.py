import databases
import sqlalchemy
import ormar

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class SchoolClass(ormar.Model):
    __tablename__ = "schoolclasses"
    __metadata__ = metadata
    __database__ = database

    id = ormar.Integer(primary_key=True)
    name = ormar.String(length=100)


class Category(ormar.Model):
    __tablename__ = "categories"
    __metadata__ = metadata
    __database__ = database

    id = ormar.Integer(primary_key=True)
    name = ormar.String(length=100)


class Student(ormar.Model):
    __metadata__ = metadata
    __database__ = database

    id = ormar.Integer(primary_key=True)
    name = ormar.String(length=100)
    schoolclass = ormar.ForeignKey(SchoolClass)
    category = ormar.ForeignKey(Category)


class Teacher(ormar.Model):
    __metadata__ = metadata
    __database__ = database

    id = ormar.Integer(primary_key=True)
    name = ormar.String(length=100)
    schoolclass = ormar.ForeignKey(SchoolClass)
    category = ormar.ForeignKey(Category)
