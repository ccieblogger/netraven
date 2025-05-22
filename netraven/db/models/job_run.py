from sqlalchemy import Column, Integer, String, JSON, Text, DateTime, ForeignKey
from netraven.db.base import Base

class JobRun(Base):
    __tablename__ = 'job_runs'
    id = Column(Integer, primary_key=True)
    job_name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    parameters = Column(JSON, nullable=False)
    output = Column(Text)

    def as_dict(self):
        return {
            'id': self.id,
            'job_name': self.job_name,
            'user_id': self.user_id,
            'timestamp': self.timestamp,
            'status': self.status,
            'parameters': self.parameters,
            'output': self.output
        }
