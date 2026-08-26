from memory.memory_models import Episode

class EpisodicMemory:

    def __init__(self):
        self.episodes: list[Episode] = []
        self.consolidated_ids: set[str] = set()

    def get_unconsolidated(self) -> list[Episode]:
        return [
            episode
            for episode in self.episodes
            if episode.episode_id not in self.consolidated_ids
        ]
    
    def mark_consolidated(self, episode: Episode):
        self.consolidated_ids.add(episode.episode_id)

    def save(self, episode: Episode):
        self.episodes.append(episode)

    def get_all(self) -> list[Episode]:
        return list(self.episodes)

    def get_by_entity(
        self,
        entity_type: str,
        entity_id: str | int | None
    ) -> list[Episode]:

        return [
            episode
            for episode in self.episodes
            if episode.entity_type == entity_type
            and episode.entity_id == entity_id
        ]

    def clear(self):
        self.episodes.clear()
        self.consolidated_ids.clear()

    def retrieve(
        self,
        question: str
    ) -> list[Episode]:
        """
        Return episodes relevant to the question.
        Uses simple keyword matching.
        """
        keywords = question.lower().split()

        return [
            episode
            for episode in self.episodes
            if any(
                word in episode.content.lower()
                for word in keywords
            )
        ]