"""
Database models and operations for Property Lead Management System.
Uses SQLAlchemy for SQLite database.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'property_leads.db')

class Property(Base):
    """Property record model."""
    __tablename__ = 'properties'
    
    id = Column(Integer, primary_key=True)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(2), default='NJ')
    zip_code = Column(String(10), nullable=False)
    owner_name = Column(String(255), nullable=True)
    owner_address = Column(String(255), nullable=True)
    
    # Property details
    property_type = Column(String(50), nullable=True)  # residential, commercial, etc.
    year_built = Column(Integer, nullable=True)
    assessed_value = Column(Float, nullable=True)
    square_footage = Column(Integer, nullable=True)
    lot_size = Column(Float, nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Float, nullable=True)
    
    # Scoring
    sell_score = Column(Float, default=0.0)  # 0-100 selling likelihood score
    score_reasons = Column(String(500), nullable=True)  # Why this score
    
    # Status
    status = Column(String(20), default='new')  # new, contacted, qualified, unqualified
    notes = Column(String(1000), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_source = Column(String(50), default='manual')
    
    def __repr__(self):
        return f"<Property({self.address}, {self.city}, Score: {self.sell_score})>"
    
    @property
    def full_address(self):
        return f"{self.address}, {self.city}, {self.state} {self.zip_code}"
    
    @property
    def mailing_address(self):
        """Address for mailing labels."""
        if self.owner_address:
            return self.owner_address
        return self.full_address


def get_engine():
    """Create database engine."""
    return create_engine(f'sqlite:///{DATABASE_PATH}', echo=False)


def init_db():
    """Initialize database tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine


def get_session():
    """Get a database session."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


# CRUD Operations

def add_property(session, **kwargs):
    """Add a new property to the database."""
    prop = Property(**kwargs)
    session.add(prop)
    session.commit()
    return prop


def get_property_by_id(session, property_id):
    """Get a property by ID."""
    return session.query(Property).filter(Property.id == property_id).first()


def get_all_properties(session, limit=None):
    """Get all properties."""
    query = session.query(Property).order_by(Property.sell_score.desc())
    if limit:
        query = query.limit(limit)
    return query.all()


def get_properties_by_city(session, city, min_score=0):
    """Get properties filtered by city and minimum score."""
    return session.query(Property).filter(
        Property.city.ilike(f'%{city}%'),
        Property.sell_score >= min_score
    ).order_by(Property.sell_score.desc()).all()


def get_properties_by_score(session, min_score=0, max_score=100):
    """Get properties filtered by score range."""
    return session.query(Property).filter(
        Property.sell_score >= min_score,
        Property.sell_score <= max_score
    ).order_by(Property.sell_score.desc()).all()


def get_filtered_properties(session, city=None, min_score=0, max_score=100, status=None):
    """Get properties with multiple filters."""
    query = session.query(Property)
    
    if city:
        query = query.filter(Property.city.ilike(f'%{city}%'))
    
    query = query.filter(
        Property.sell_score >= min_score,
        Property.sell_score <= max_score
    )
    
    if status:
        query = query.filter(Property.status == status)
    
    return query.order_by(Property.sell_score.desc()).all()


def update_property(session, property_id, **kwargs):
    """Update a property record."""
    prop = get_property_by_id(session, property_id)
    if prop:
        for key, value in kwargs.items():
            if hasattr(prop, key):
                setattr(prop, key, value)
        prop.updated_at = datetime.utcnow()
        session.commit()
    return prop


def delete_property(session, property_id):
    """Delete a property record."""
    prop = get_property_by_id(session, property_id)
    if prop:
        session.delete(prop)
        session.commit()
        return True
    return False


def get_cities(session):
    """Get list of all cities in database."""
    results = session.query(Property.city).distinct().all()
    return sorted([r[0] for r in results if r[0]])


def get_stats(session):
    """Get database statistics."""
    total = session.query(Property).count()
    avg_score = session.query(Property).with_entities(
        sqlalchemy.func.avg(Property.sell_score)
    ).scalar() or 0
    
    return {
        'total_properties': total,
        'average_score': round(float(avg_score), 2),
        'cities': len(get_cities(session))
    }


import sqlalchemy

if __name__ == '__main__':
    # Initialize database
    init_db()
    print("Database initialized successfully!")
    print(f"Database path: {DATABASE_PATH}")