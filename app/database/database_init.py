import logging

from sqlalchemy.engine import Engine

from app.core.config import settings
from app.database import Base
from app.database import get_engine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

def init_db(engine: Engine) -> None:

    Base.metadata.create_all(bind=engine)

def drop_db(engine: Engine) -> None:

    if settings.DROP_DB:
        logger.info('Dropping database...')
        Base.metadata.drop_all(bind=engine)

if __name__ == '__main__':

    # no cover is specified in the example code, which makes sense as this is a main method

    engine = get_engine() # pragma: no cover
    drop_db(engine=engine) # pragma: no cover
    init_db(engine=engine) # pragma: no cover
