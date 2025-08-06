# multi_plutchik_plotter.py

import matplotlib.pyplot as plt
from pyplutchik import plutchik


class PlutchikPlotter:
    BASE_EMOTIONS = [
        'joy', 'trust', 'fear', 'surprise',
        'sadness', 'disgust', 'anger', 'anticipation'
    ]

    def __init__(self, emotion_sets, labels=None):
        """
        Initialize emotion wheel plotting class, only for drawing multiple emotion distributions on the same figure/ax
        :param emotion_sets: List, each element is an emotion score dictionary
        :param labels: Corresponding label list
        """
        self.emotion_sets = emotion_sets
        self.labels = labels or [f"Set {i+1}" for i in range(len(emotion_sets))]

    def draw_multiple_plutchik_wheels(self,return_fig=False):
        """
        Draw multiple emotion distributions on the same figure/ax.
        """
        print("Drawing multiple emotion distributions, emotion score dictionary list:", self.emotion_sets)
        fig = plt.figure(figsize=(8, 8))
        ax = plt.subplot(111)
        handles = []
        for i, emotion_scores in enumerate(self.emotion_sets):
            if not emotion_scores:
                print(f"Group {i+1} emotion distribution is empty, skipping drawing.")
                continue
            patches = plutchik(
                emotion_scores,
                ax=ax
            )
            if isinstance(patches, list) and patches:
                handles.append(patches[0])
        if handles:
            ax.legend(handles, self.labels, loc='upper right', bbox_to_anchor=(1.2, 1.1))
        ax.set_aspect('equal')  # Ensure circular shape
        plt.tight_layout()
        if return_fig:
            return fig  # ✅ Key: return fig for main function to save image
        else:
            plt.show()  # Use for debugging, disable in production environment

