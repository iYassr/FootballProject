import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Club, Base, Player, User

engine = create_engine('sqlite:///Clubs.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


data = pd.read_csv('data.csv')
# Create dummy user

User1 = User(name="Yasser", email="Yasserd@gmail.com",
             picture='http://museumsassn.bc.ca/wp-content/uploads/2018/01/BCMA-Avatar-400px.png')
session.add(User1)
session.commit()


Club2 = Club(user_id=1, name="Arsenal")
session.add(Club2)
session.commit()


Club1 = Club(user_id=1, name="Chelsea")
session.add(Club1)
session.commit()


Club3 = Club(user_id=1, name="Everton")
session.add(Club3)
session.commit()

Club4 = Club(user_id=1, name="Huddersfield")
session.add(Club4)
session.commit()


for index, row in data.iterrows():
    player = Player(user_id=1, name=row['name'], club_id=row['club'], nationality=row['nationality'],
                    age=row['age'], position=row['position_cat'], market_value=int(row['market_value']))
    session.add(player)
    session.commit()

print("added players!")
