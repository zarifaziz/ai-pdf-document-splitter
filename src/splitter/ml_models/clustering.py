from typing import List

import numpy as np
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import AgglomerativeClustering


def custom_distance(
    embedding1: np.ndarray, embedding2: np.ndarray, alpha: float
) -> float:
    """
    Calculate a custom distance between two embeddings, considering both embedding distance and page distance.

    Args:
        embedding1 (np.ndarray): The first embedding with the page number as the first element.
        embedding2 (np.ndarray): The second embedding with the page number as the first element.
        alpha (float): Weighting factor between embedding distance and page distance.

    Returns:
        float: The calculated custom distance.
    """
    page_num1, emb1 = int(embedding1[0]), embedding1[1:]
    page_num2, emb2 = int(embedding2[0]), embedding2[1:]
    embedding_distance = np.linalg.norm(emb1 - emb2)
    page_distance = abs(page_num1 - page_num2)
    return float(alpha * embedding_distance + (1 - alpha) * page_distance)


def post_process_labels(labels: np.ndarray, page_gap_threshold: int) -> np.ndarray:
    """
    Post-process the clustering labels to split clusters with large page gaps.

    Args:
        labels (np.ndarray): Initial clustering labels.
        page_gap_threshold (int): Threshold for the page gap to split clusters.

    Returns:
        np.ndarray: The post-processed clustering labels.
    """
    final_labels = np.copy(labels)
    current_label = max(labels) + 1
    for cluster in np.unique(labels):
        cluster_indices = np.where(labels == cluster)[0]
        for i in range(1, len(cluster_indices)):
            if cluster_indices[i] - cluster_indices[i - 1] > page_gap_threshold:
                final_labels[cluster_indices[i:]] = current_label
                current_label += 1
                break
    return final_labels


def perform_clustering(
    embeddings: List[np.ndarray],
    alpha: float = 0.9,
    distance_threshold: float = 2.1,
    page_gap_threshold: int = 1,
) -> np.ndarray:
    """
    Perform agglomerative clustering on the given embeddings with a custom distance metric.

    Args:
        embeddings (List[np.ndarray]): List of embeddings to cluster.
        alpha (float, optional): Weighting factor between embedding distance and page distance. Defaults to 0.9.
        distance_threshold (float, optional): Threshold to apply when forming flat clusters. Defaults to 1.5.
        page_gap_threshold (int, optional): Threshold for the page gap to split clusters. Defaults to 1.

    Returns:
        np.ndarray: The final clustering labels after post-processing.
    """
    page_numbers = np.arange(len(embeddings)).reshape(-1, 1)
    embeddings_with_pages = np.hstack((page_numbers, np.array(embeddings)))

    # Compute the custom distance matrix
    distance_matrix = squareform(
        pdist(embeddings_with_pages, lambda x, y: custom_distance(x, y, alpha))
    )

    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric="precomputed",
        linkage="average",
    )
    labels = clustering.fit_predict(distance_matrix)

    # not needed once page_distance was introduced
    # labels = post_process_labels(labels, page_gap_threshold)

    return labels
