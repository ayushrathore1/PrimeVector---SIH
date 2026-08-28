from abc import ABC, abstractmethod
import random
from typing import List

WORD_POOL = ['alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf', 'hotel',
             'india', 'juliet', 'kilo', 'lima', 'mike', 'november', 'oscar', 'papa',
             'quebec', 'romeo', 'sierra', 'tango', 'uniform', 'victor', 'whiskey',
             'xray', 'yankee', 'zulu', 'orange', 'bicycle', 'mountain', 'paper',
             'garden', 'silver', 'thunder', 'crystal', 'dolphin', 'compass']

class LivenessChecker(ABC):
    @abstractmethod
    def generate_challenge(self) -> str: ...
    
    @abstractmethod
    def verify(self, challenge: str, audio_embedding: List[float]) -> bool: ...

class StubLivenessChecker(LivenessChecker):
    """Always passes. Replace with real implementation."""
    def generate_challenge(self) -> str:
        return ' '.join(random.sample(WORD_POOL, k=5))
    
    def verify(self, challenge: str, audio_embedding: List[float]) -> bool:
        return True
