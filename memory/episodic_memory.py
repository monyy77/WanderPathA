from memory.memory_models import Episode

class EpisodicMemory:

    def __init__(self):
        self.episodes: list[Episode] = []

    def save(self, episode: Episode):
        self.episodes.append(episode)

    def get_all(self) -> list[Episode]:
        return list(self.episodes)

    def get_by_entity(
        self,
        entity_type: str,
        entity_id: int
    ) -> list[Episode]:

        return [
            episode
            for episode in self.episodes
            if episode.entity_type == entity_type
            and episode.entity_id == entity_id
        ]

    def clear(self):
        self.episodes.clear()
