
# MRD: Multi-resolution Retrieval-Detection Fusion for High-Resolution Image Understanding

| Fan Yang<br/>Harbin Institute of Technology (Shenzhen)<br/>25b951055\@stu.hit.edu.cn | Kaihao Zhang<br/>Harbin Institute of Technology (Shenzhen)<br/>super.khzhang\@gmail.com |
| ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |


## Abstract

*Understanding high-resolution images remains a significant challenge for multimodal large language models (MLLMs). Recent study address this issue by dividing the image into smaller crops and computing the semantic similarity between each crop and a query using a pretrained retrieval-augmented generation (RAG) model. The most relevant crops are then selected to localize the target object and suppress irrelevant information. However, such crop-based processing can fragment complete objects across multiple crops, thereby disrupting the computation of semantic similarity. In our experiments, we find that image crops of objects with different sizes are better handled at different resolutions. Based on this observation, we propose Multi-resolution Retrieval-Detection (MRD), a trainingfree framework for high-resolution image understanding. To address the issue of semantic similarity bias caused by objects being split across different image crops, we propose a multi-resolution semantic fusion method, which integrates semantic similarity maps obtained at different resolutions to produce more accurate semantic information and preserve the integrity of target objects. Furthermore, to achieve direct localization of target objects at a global scale, we introduce an open-vocabulary object detection (OVD) model that identifies object regions using a sliding-window approach.Experiments on high-resolution image understanding benchmarks using different MLLMs demonstrate the effectiveness of our approach.*

## 1. Introduction

Multimodal Large Language Models (MLLMs) have demonstrated significant advancements in integrating and interpreting visual and linguistic information, enabling robust capabilities in vision-language understanding, reasoning, and interactive tasks [25]. By leveraging visual signals, these models can process and decipher complex visual information, forming a bridge between pixel-level data and

| **Query: Is the red vehicle on the left or right side of the image?**<br/>**High-Resolution Image** |                                                                          | **Semantic Map**<br/>**RAG** |                   |
| --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ---------------------------- | ----------------- |
| MLLM                                                                                                | OVD                                                                      |                              | **Detection Map** |
|                                                                                                     | The red vehicle is on the<br/>right side of the image.<br/>**RE-Search** |                              |                   |


Figure 1. Overview of the proposed Multi-resolution Retrieval-Detection framework, which uses RAG and OVD to obtain semantic similarity map and detection confidence map respectively. By integrating the two, the target objects can be localized more accurately.

semantic interpretation [17, 20]. However, a common practice among most MLLMs is to process input images at fixed and pre-defined resolutions [1, 13, 14]. While this uniform input pipeline simplifies model architecture and reduces computational overhead, it introduces substantial limitations. Specifically, resizing high-resolution (HR) real-world images to a fixed low resolution often leads to shape distortion and blurring, which degrades the quality of fine-grained visual details. Recent studies [11, 19, 22, 24, 29, 30] indicate that existing methods remain unsatisfactory for highresolution image tasks. This is clearly demonstrated by their suboptimal results on dedicated high-resolution image understanding benchmarks [21, 24].

To address this limitation, improving the high-resolution image perception capability of MLLMs has become an emerging research focus. A common "locate-and-zoomin" strategy is widely adopted to enhance detail perception in models. Although training-based approaches such as Supervised Fine-Tuning (SFT) [18] and Reinforcement




Learning (RL) [30] can effectively identify relevant regions, they are hampered by critical limitations, including high computational costs, long training cycles, and poor cross-architecture transferability, which curtails their scalability and practical application. In contrast, training-free methods [11, 19, 29] automatically locate regions by using attention mechanisms or tree-based search, without requiring the construction of the dataset or the fine-tuning of the model. Despite employing a top-down search strategy from high to low resolution, these methods face significant limitations. A primary issue is the model's inadequate perception of small objects during the initial search stage [19, 21], which frequently leads to the generation of erroneous search paths.

Recently, Inspired by the success of Retrieval-Augmented Generation (RAG) for enabling long-context understanding in general LLMs [9], Wang et al. [22] introduced Retrieval-Augmented Perception (RAP) — a training-free framework designed to enhance MLLMs' perception of high-resolution images. RAP extends this paradigm to the visual domain, achieving significant performance improvement on high-resolution benchmarks. The RAP framework consists of three key components: First, the Visual Retrieval module employs a pre-trained vision RAG model, VisRAG, to compute semantic similarity between the query and different image regions (crops), retrieving the most relevant ones to reduce noise. Next, the Spatial-Awareness Layout module preserves the original relative spatial relationships among the retrieved crops when composing them into the model input, maintaining spatial coherence. Finally, the Adaptive Retrieval-Exploration Search (RE-Search) module dynamically determines the optimal number of retrieved crops by constructing a Retrieval-Exploration Tree (RE-Tree), balancing information sufficiency with computational efficiency.

Despite its promise, the RAP method suffers from several inherent limitations. First, the patching operation can fragment large objects across multiple disjointed crops, disrupting their holistic semantics and leading to biased similarity calculations. Our empirical observations confirm that some patches semantically irrelevant to the query can obtain abnormally high similarity scores. Second, the patch resolution is a critical yet difficult-to-tune hyperparameter: overly large patches introduce redundant background information, while overly small ones exacerbate object fragmentation. Experiments show that the choice of resolution significantly impacts performance. Third, in high-resolution images with cluttered backgrounds, the similarity measure is prone to false positives, where background regions may attain higher similarity than those containing the actual target objects, severely hampering recognition.

To tackle these challenges, we propose a novel Multi-resolution Retrieval-Detection (MRD) framework, based on RAP to improve retrieval quality and localization accuracy through two key techniques:

• Multi-resolution Semantic Fusion: To mitigate the bias inherent in single-resolution patching, we design a simple yet effective fusion strategy. It computes semantic similarities across multiple proportional resolutions and performs consistency-based fusion to calibrate the results, yielding a more robust and accurate relevance estimation that alleviates semantic deviations caused by object fragmentation.

• Open-vocabulary Detector Enhancement: For more precise target localization, we incorporate an advanced open-vocabulary object detector, LLMDet [7]. First, we leverage the in-context learning capability of LLMs to extract target concepts from the query, defining the categories for the detector. Subsequently, a sliding window mechanism is employed to traverse the entire high-resolution image, detecting target objects within each window to generate a confidence map indicating target presence.

Finally, the calibrated multi-resolution semantic similarity is augmented by the object detection confidence. This synergistic fusion effectively amplifies the response in true target regions, enabling faster and more accurate localization of critical areas during subsequent retrieval, thereby guiding the MLLM toward more reliable inference.

We conduct extensive experiments on several high-resolution benchmarks, including V* [24], HRBench-4K, and HRBench-8K [21], utilizing various MLLMs such as LLaVA-ov and LLaVA-v1.5. The results demonstrate that our MRD framework surpasses all existing training-free methods and achieves state-of-the-art performance on both single-object and multi-object retrieval and recognition tasks, with particularly notable gains on single-object tasks.

Our contributions are summarized as follows:

• To the best of our knowledge, this is the first work that systematically leverages an open-vocabulary object detector to enhance MLLMs' understanding of high-resolution images. Experiments validate that the detector provides precise target localization, effectively suppressing interference from irrelevant regions.

• We propose MRD, a training-free and generic framework. It innovatively corrects semantic similarity via a multi-resolution fusion strategy and integrates open-set detection results to enhance target regions, creating a synergistic effect.

• Comprehensive experiments validate the effectiveness and generalization of our method. It achieves leading performance on both single-object and multi-object tasks across different MLLMs and high-resolution benchmarks.




## 2. Related Work

### 2.1. Multimodal Large Language Models

MLLMs have rapidly advanced as powerful foundation models capable of understanding and generating multimodal content across diverse vision-language tasks [25, 28]. Early MLLM architectures generally adopt fixed-resolution vision encoders—such as 224 × 224 or 448 × 448 ViTs [2, 12–14]. While this design simplifies training and computation, it inevitably requires resizing or cropping high-resolution (HR) images, thereby discarding fine-grained visual details crucial for tasks such as fine-grained recognition, dense reasoning, or detecting small objects.

To enhance high-resolution image understanding without proportionally increasing the computational burden from visual tokens, several studies have integrated high-resolution visual encoders into MLLMs. For example, Vary [23] and Deepseek-VL [15] incorporate the SAM encoder [10] to improve model performance on HR images.

Alternatively, another line of work introduced Native/Dynamic-Resolution MLLMs that processes images at their native resolution. The core idea is to generate a variable-length sequence of visual tokens that adapts to the original dimensions of the input image, thereby preserving spatial fidelity and high-frequency details. These models employ various mechanisms to handle the resulting long sequences and computational complexity, including sliding window attention, dynamic masking, and patch-based encoding strategies. Representative works in this category have demonstrated significant progress. For instance, the InternVL series [4, 6, 31] adopts a strategy of splitting a high-resolution image into multiple fixed-size patches. In contrast, models like Qwen2.5-VL [2, 3] take an end-to-end approach by training a ViT directly on native-resolution images. This allows the model to embed the entire image into a single, coherent token sequence in one forward pass, potentially leading to better global context understanding.

### 2.2. High-Resolution Image Understanding

Multimodal large language models (MLLMs) have made substantial progress in recent years; however, they continue to face challenges in accurately recognizing and interpreting fine-grained details within high-resolution (HR) images [21?]. To enhance the capability of MLLMs in high-resolution image understanding, existing studies generally follow two main directions. Training-based approaches rely on supervised fine-tuning (SFT) [18, 24] or reinforcement learning (RL) [30], but such methods often compromise the model's generalization ability on broad vision–language tasks. In contrast, training-free approaches [11, 19, 21, 22]typically perform hierarchical or tree-based search to localize target regions. However, these methods tend to suffer from low efficiency and may fail to retain all target objects during the search process, particularly in multi-object scenarios.

## 3. Preliminary

In this section, We first conduct an analysis of the relationship between the resolution of image crops and the performance of MLLMs in subsection 3.2. The experimental results indicate that using different resolution has a significant impact on MLLMs to analyze HR images. Objects of different sizes are suitable for different resolutions. Inspired by this we propose the MRD framework.

### 3.1. Semantic Similarity

This section presents the pipeline for integrating Retrieval-Augmented Generation (RAG) into Multimodal Large Language Models (MLLMs) to calculate the semantic similarity scores between the query embedding and images crops from HR images. Given an HR image, we first partition it collection of image patches, denoted as $$P = \{p_1, p_2, \ldots, p_n\}$$, where $$n$$ is the total number of image crops. Following the approach of Yu et al. [27], the textual query and each image crop are encoded independently using the text and image encoders of a Vision-Language Model (VLM), producing a sequence of hidden representations. The semantic similarity score between the query embedding and each image crop embedding is then computed. Specifically, the similarity score $$s(q, p_i)$$ for the i-th crop is calculated by the cosine similarity of the query and image crop embeddings:

$$s(q, p_i) = \frac{1}{2} \cdot (1 + \frac{q \cdot p_i}{\|q\| \cdot \|p_i\|})$$
(1)

Based on these scores, the top $$K$$ most relevant image crops are selected and provided to the MLLM to support detailed understanding of the high-resolution input.

### 3.2. Impact of the Resolution of Image Crops

In this section, we conduct an analysis to investigates the relationship between the resolution of image crops and the performance of MLLMs in HR image understanding.

**Experimental setting.** We analyze the relation between performance and the resolution of image crops, using LLaVA-ov and LLaVA-v1.5 on V * benmark.

**Observations.** We visualize the relationship between the resolution of image crops and performance of MLLMs. As shown in Figure 3, from the overall accuracy obtained by using different resolutions, when the resolution of image crops is set to 112, using different MLLM achieved the highest accuracy rates in both the single-object task and the multi-object task. This indicates that setting the resolution to 112 might be the optimal choice. However, when we take





| ![Street scene with half-timbered buildings and baby carriage](image1)                                                                                                                                                                   | ![Building facade detail](image2) | ![Building entrance with baby carriage](image3) | **Semantic Similarity**<br/>![Semantic similarity heatmap showing building in blue tones](heatmap) |                                                     | ![Building detail in green/blue tones](image4) |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------- | --------------------------------------------------- | ---------------------------------------------- |
| **What is the color of the baby carriage?**<br/>A. The color of the baby carriage is black.<br/>B. The color of the baby carriage is green.<br/>C. The color of the baby carriage is red.<br/>D. The color of the baby carriage is blue. |                                   | **Answer: B**<br/>**Resolution=96**             | **Answer: B**<br/>**Resolution=112**                                                               | **Resolution =112**<br/>![Scale from 0 to 1](scale) | ![Sad face emoji](sad_face)                    |
|                                                                                                                                                                                                                                          | ![Street scene detail](image5)    | **Answer: B**<br/>**Resolution =144**           | **Answer: A**<br/>**Resolution =224**                                                              |                                                     |                                                |


Figure 2. Setting the resolution of image crops to 112 causes complete objects to be split across different regions, which disrupts the semantic information of the target objects.

| **Attribute**                                                                                      |   |   | **Spatial**                                |   |   |
| -------------------------------------------------------------------------------------------------- | - | - | ------------------------------------------ | - | - |
| ![Two line graphs showing Accuracy vs Resolution of Image Crop for different LLaVA models](graphs) |   |   |                                            |   |   |
| LLaVA-ov-0.5B LLaVA-v1.5-7B LLaVA-v1.5-13B                                                         |   |   | LLaVA-ov-0.5B LLaVA-v1.5-7B LLaVA-v1.5-13B |   |   |


Figure 3. The effect of the resolution of retrieved image crops on model performance. Attribute and Spatial represent the attribute recognition and spatial reasoning in $$V^*$$ Bench.

a closer look at the results of each sample, we find that in some cases, choosing a different resolution actually leads to more accurate results compared to when the resolution is 112, as shown in Figure 3. The results of the image crops selected based on different resolutions and the visualization of the semantic similarity map can provide a very intuitive analysis of the reasons: Since the complete object is divided into different crops, some parts of it have a higher semantic similarity calculated by VisRAG, while other parts have a lower semantic similarity. After screening, only the parts with higher similarity are retained. However, this will damage the integrity of the target object and cause interference to the judgment of MLLM.

## 4. Method

In this section, we propose a novel framework named Multi-resolution Retrieval Detection (MRD). The core design of MRD lies in its multi-resolution approach at different scales to better localize regions containing target objects. This enables subsequent search processes to more easily identify image crops corresponding to the target objects, eliminating irrelevant distractions and enhancing the perceptual understanding of HR images by MLLMs. Based on the findings in subsection 3.2, we argue that using different resolutions for semantic similarity computation is more suitable for objects of varying sizes and locations. Inspired by this idea, we first introduce a simple yet effective Multi-resolution Semantic Fusion method, which computes semantic similarity maps at different resolutions on a local scale and performs consistency-based fusion to refine the semantic similarity and improve its accuracy. To more directly localize target objects, we incorporate an Open-vocabulary object detection model that traverses the entire HR image globally using a sliding window approach, generating confidence scores for regions containing target objects. Finally, by integrating the detection confidence scores with the multi-resolution semantic similarity maps, our method not only improves localization of target regions but also distinguishes fine-grained differences among crops in these regions, thereby assisting subsequent search processes in more accurately identifying key areas. The following sections will provide detailed explanations of each component.

### 4.1. Multi-resolution Semantic Fusion

In subsection 3.2, we observe that image crops of different resolutions are suitable for objects of varying sizes and locations in different cases. Compared to the semantic similarity map obtained using a single resolution, those derived from multiple resolutions exhibit respective advantages. Therefore, we first propose a Multi-Resolution Semantic Fusion method. As shown in the top part of Figure 4, we partition the HR image using proportional resolutions, with the low resolution set to $$l$$ and the high resolution set to $$\hat{l}$$, where







Figure 4. Detailed information of our proposed *MRD*. First, We use VisRAG with different resolution of image crops to obtain multi-resolution semantic similarity map. We then employ an open-set object detection model, LLMDet, to localize the target objects extracted from the query within the high-resolution image using a sliding-window approach, yielding a global detection confidence map. Finally, the obtained multi-resolution semantic similarity map is linearly fused with the detection confidence map, and the fused scores are used to guide the subsequent search to select image crops containing the target objects.

$$\hat{l} = k \cdot l$$. The set of image patches at high resolution is denoted as $$\hat{P} = \{\hat{p}_1, \hat{p}_2, \ldots, \hat{p}_m\}$$, and at low resolution as $$P = \{p_1, p_2, \ldots, p_n\}$$. Due to the proportional relationship between high and low resolutions, we have $$n = k^2 \cdot m$$, and each high-resolution patch $$\hat{p}_i$$ corresponds to $$k^2$$ low-resolution patches:

$$\hat{p}_i = \begin{bmatrix} \tilde{p}_{i,1} & \tilde{p}_{i,2} & \cdots & \tilde{p}_{i,k} \\ \tilde{p}_{i,(k+1)} & \tilde{p}_{i,(k+2)} & \cdots & \tilde{p}_{i,(2k)} \\ \vdots & \vdots & \ddots & \vdots \\ \tilde{p}_{i,(k(k-1)+1)} & \tilde{p}_{i,(k(k-1)+2)} & \cdots & \tilde{p}_{i,k^2} \end{bmatrix}$$ (2)

where $$\tilde{p}_{ij} \in P, i \in \{1, 2, \ldots, m\}, \quad j \in \{1, 2, \ldots, k^2\}$$.

Then, using Equation 1, we compute the cosine similarity between the query and image crop embeddings to obtain the semantic similarity scores for high and low resolutions, respectively: $$\hat{S} = \{\hat{s}_1, \hat{s}_2, \ldots, \hat{s}_m\}$$ and $$S = \{s_1, s_2, \ldots, s_n\}$$:

$$\hat{s}_i = s(f(q), g(\hat{p}_i)), \quad s_j = s(f(q), g(p_j))$$ (3)

where $$f(\cdot)$$ and $$g(\cdot)$$ denote the embedding operations for the query and image crop, respectively, with $$i \in \{1, 2, \ldots, m\}$$ and $$j \in \{1, 2, \ldots, n\}$$. According to the mapping from $$\hat{p}_i$$ to $$p_j$$ in (2), we can map the semantic similarity $$\hat{s}$$ obtained from each high-resolution $$\hat{p}$$ and the query to the corresponding $$k^2$$ low-resolution $$p$$ positions. The mapping operation can be expressed as:

$$\tilde{S} = H(\hat{S})$$ (4)

where $$\tilde{S} = \{\tilde{s}_1, \tilde{s}_2, \ldots, \tilde{s}_n\}$$. After obtaining $$\tilde{S}$$ and $$S$$, we perform consistency fusion on the semantic similarities at corresponding positions to obtain the multi-resolution semantic similarity $$S^f = \{s^f_1, s^f_2, \ldots, s^f_n\}$$, which can be expressed as:

$$s^f_t = \sqrt{\tilde{s}_t \cdot s_t}, \quad t \in 1, 2, \ldots, n$$ (5)

Finally, we can transform the semantic similarity scores into a two-dimensional semantic similarity map $$s^f(i, j)$$ with $$i \in \{1, 2, \ldots, H\}$$ and $$j \in \{1, 2, \ldots, W\}$$. The total number of low resolution image crop $$n = H \times W$$.

Fusing the multi-resolution semantic similarity scores from high and low resolutions enables correction of the low-resolution similarities when a complete object is split across different patches in the low-resolution view. This enhances the similarity of various parts of the object, thereby preserving the integrity of the object as much as possible during subsequent search processes and improving the recognition accuracy of the MLLM.

## 4.2. Open-vocabulary Detector Enhancement

VisRAG divides the HR image into patches and computes semantic similarity between the query and each image crop,




enabling localized object retrieval at a small scale. However, it struggles to accurately localize larger objects. To address this limitation and achieve more direct and large-scale object localization, we introduce an advanced open-vocabulary object detection model—LLMDet—to directly locate regions containing target objects. First, we employ in-context learning with a Large Language Model (LLM) to extract the primary target objects from the query, which serve as the target categories for LLMDet. Due to the extremely high resolution of HR images in datasets such as HR-Bench, we adopt a sliding window strategy for object localization. To align with the semantic similarity map derived from image crops, we assign the detection confidence scores of the target bounding boxes to their corresponding image patches, thereby generating a detection map that reflects the confidence of target object presence in each patch. This detection map offers a more intuitive localization representation compared to the semantic similarity map. In the following, we provide a detailed introduction to the proposed method.

**Object Extraction.** To enable open-vocabulary object detection, we first leverages Large Language Models (LLMs) to dynamically identify target objects from textual queries. Given an input query $Q$, we employ in-context learning to extract the primary object entities that serve as detection targets for our LLMDet framework.

Formally, we define the object extraction process as:

$$O = \text{LLM}(\mathcal{P}_{\text{system}}, \mathcal{E}_{\text{examples}}, Q) \tag{6}$$

where $O$ represents the set of extracted objects, $\mathcal{P}_{\text{system}}$ denotes the system prompt containing extraction guidelines, and $\mathcal{E}_{\text{examples}}$ constitutes the demonstration examples.

**Sliding-window Object Detection.** In order to get a global detection confidence map align with the previously semantic similarity map, we similarly partition the HR image into a grid of $H \times W$ non-overlapping patches where total number of patches $n = H \times W$. A sliding window of size $h \times w$ patches (where $h < H$ and $w < W$) traverses the entire image with a predefined stride. In this way, We can obtain $T$ sliding windows $W = \{W_1, W_2, ..., W_T\}$.

After obtaining multiple sliding windows using the sliding window method, we use LLMDet to detect objects within each sliding window. The detector generates a set of bounding boxes $\mathcal{B}_t = \{b_1, b_2, \ldots, b_{K_t}\}$ and the corresponding confidence scores $s_k$ indicating the likelihood of containing a target object where $t$ denotes the $t$-th sliding window.

We apply a confidence threshold $\tau$ to filter out low-quality detections:

$$\mathcal{B}_t^{\text{filter}} = \{b_k \in \mathcal{B}_t \mid s_k > \tau\} \tag{7}$$

Subsequently, we generate a window detection confidence map $\mathbf{c}_t^w \in \mathbb{R}^{h \times w}$ for the current window. The value

at patch coordinate $(p, q)$ within this local window is assigned the maximum confidence score among all bounding boxes in $\mathcal{B}_t^{\text{filter}}$ that contain this patch. If no box covers the patch, the confidence is set to 0:

$$\mathbf{c}_t^w(p, q) = \max_{b_k \in \mathcal{B}_t^{\text{filter}}} \{s_k \cdot \mathbb{I}[(m, n) \in b_k]\} \tag{8}$$

where $\mathbb{I}[\cdot]$ is the indicator function that equals 1 if the patch $(p, q)$ is inside the bounding box $b_k$, and 0 otherwise.

To aggregate information from all sliding windows and form a global, unified detection confidence map $\mathbf{c}^g \in \mathbb{R}^{H \times W}$ for the entire high-resolution image, we employ an averaging fusion strategy. For a global patch at coordinate $(p, q)$, its final confidence score is computed as the average of all confidence scores assigned to it from every sliding window that contained it.

For the patch $I(i, j)$ at position $(i, j)$ in the HR image, if it is contained in the $t$-th sliding window, we denote its position in the $t$-th sliding window $W_t$ as $(t_i, t_j)$, which can be expressed as

$$I(i, j) = W_t(t_i, t_j), \quad t \in \mathcal{T}_{i,j} \tag{9}$$

where $\mathcal{T}_{ij}$ denotes the set of sliding windows that contain $I(i, j)$. Now, we can obtain the global detection confidence map of the whole HR image, which can be computed as:

$$\mathbf{c}^g(i, j) = \frac{1}{|\mathcal{T}_{i,j}|} \sum_{t \in \mathcal{T}_{i,j}} \mathbf{c}_t^w(t_i, t_j) \tag{10}$$

where $i \in \{1, 2, \ldots, H\}$ and $j \in \{1, 2, \ldots, W\}$.

The detection confidence map provides effective localization of target regions on a global scale, offering direct spatial guidance but lacking the ability to distinguish fine-grained differences within the target object. To address this limitation, we integrate the detection confidence with multi-resolution semantic similarity through linear combination, which can be expressed as:

$$\mathbf{s}^F(i, j) = (1 - w) \cdot \mathbf{s}^f(i, j) + w \cdot \mathbf{c}^g(i, j) \tag{11}$$

This synergistic fusion enables precise target localization while effectively highlighting intra-object variations, thereby facilitating more accurate extraction of key regions in subsequent search processes. The details of the subsequent Retrieved-Exploration Search process can be found in paper [22].

## 5. Experiments

**Evaluated benchmark.** We evaluate our *MRD* on two high-resolution benchmarks. The first is $V^*$ *Bench* [24], with an average resolution of $2246 \times 1582$, consists of two sub-tasks: attribute recognition and spatial reasoning. The Second is HRBench which includes two sub-task Fine-grained Single-instance Perception (FSP) and Fine-grained Cross-instance Perception (FCP).




Table 1. Comparison of *MRD* with existing works on high-resolution benchmarks

| Method                       | V\* Bench<br/>Attribute | V\* Bench<br/>Spatial | V\* Bench<br/>Overall | HR-Bench 4K<br/>FSP | HR-Bench 4K<br/>FCP | HR-Bench 4K<br/>Overall | HR-Bench 8K<br/>FSP | HR-Bench 8K<br/>FCP | HR-Bench 8K<br/>Overall |
| ---------------------------- | ----------------------- | --------------------- | --------------------- | ------------------- | ------------------- | ----------------------- | ------------------- | ------------------- | ----------------------- |
| *Open-source MLLMs*          |                         |                       |                       |                     |                     |                         |                     |                     |                         |
| LLaVA-v1.6-7B \[14]          | 60.9                    | 63.2                  | 61.8                  | 49.0                | 46.8                | 47.9                    | 37.3                | 44.3                | 40.8                    |
| LLaVA-v1.6-13B \[14]         | 60.0                    | 64.5                  | 61.8                  | 49.8                | 41.3                | 45.5                    | 38.0                | 38.3                | 38.1                    |
| LLaVA-v1.6-34B \[14]         | -                       | -                     | -                     | 55.3                | 50.5                | 52.9                    | 44.5                | 50.3                | 47.4                    |
| LLaVA-HR-X-13B \[16]         | -                       | -                     | -                     | 61.3                | 46.0                | 53.6                    | 49.5                | 44.3                | 46.9                    |
| LLaVA-HR-X-7B \[16]          | 51.3                    | 64.5                  | 56.5                  | 57.8                | 46.3                | 52.0                    | 42.0                | 41.3                | 41.6                    |
| InternVl-1.5-26B \[5]        | -                       | -                     | -                     | 69.5                | 51.8                | 60.6                    | 69.3                | 48.5                | 57.9                    |
| Yi-VL-34B \[26]              | -                       | -                     | -                     | 46.0                | 42.8                | 44.4                    | 39.5                | 38.5                | 39.0                    |
| *Closed-source MLLMs*        |                         |                       |                       |                     |                     |                         |                     |                     |                         |
| GPT-4o \[8]                  | -                       | -                     | 66.0                  | 70.0                | 48.0                | 59.0                    | 62.0                | 49.0                | 55.5                    |
| Qwen-VL-max \[2]             | -                       | -                     | -                     | 65.0                | **52.0**            | 58.5                    | 54.0                | **51.0**            | 52.5                    |
| *Baselines and MRD*          |                         |                       |                       |                     |                     |                         |                     |                     |                         |
| LLaVA-v1.5-7B \[14]          | 43.5                    | 56.6                  | 48.7                  | 38.5                | 33.8                | 36.1                    | 33.0                | 31.3                | 32.1                    |
| LLaVA-v1.5-7B-Zoom Eye \[19] | 83.5                    | 82.9                  | 83.3                  | 67.8                | 38.8                | 53.3                    | 65.5                | 36.0                | 50.8                    |
| LLaVA-v1.5-7B-RAP \[22]      | 90.4                    | **96.1**              | 91.1                  | 73.8                | 40.5                | 57.1                    | 72.3                | 35.3                | 53.8                    |
| **LLaVA-v1.5-7B-MRD (ours)** | **97.4**                | **96.1**              | **95.6**              | **76.8**            | 42.7                | **59.7**                | **72.6**            | 37.2                | **54.9**                |
| LLaVA-ov-0.5B \[14]          | 63.5                    | 64.5                  | 63.9                  | 63.5                | 39.5                | 51.5                    | 47.3                | 38.3                | 42.8                    |
| LLaVA-ov-0.5B-Zoom Eye\[19]  | 85.2                    | 73.7                  | 80.6                  | 75.5                | 39.8                | 57.6                    | 68.5                | 38.3                | 53.4                    |
| LLaVA-ov-0.5B-RAP \[22]      | 80.0                    | 84.2                  | 83.6                  | 80.3                | 42.3                | 61.3                    | **81.8**            | 45.3                | 63.5                    |
| **LLaVA-ov-0.5B-MRD (ours)** | **89.6**                | **82.9**              | **88.0**              | **84.0**            | **45.2**            | **64.6**                | **81.8**            | **47.3**            | **64.5**                |


| **HR Image**                                                   | **Res = 112** | **Res = 224** | **Multi-res** |   | **Search Result<br/>(Res = 112)** | **Search Result<br/>(Multi-res)** |
| -------------------------------------------------------------- | ------------- | ------------- | ------------- | - | --------------------------------- | --------------------------------- |
| What is the color of the cyclist's box?                        |               |               |               |   |                                   |                                   |
| Is the green bucket on the left or right side of the red tent? |               |               |               |   |                                   |                                   |
| **HR Image**                                                   | **Res = 112** | **OVD**       | **RAG+OVD**   |   | **Search Result<br/>(Res = 112)** | **Search Result<br/>(RAG+OVD)**   |
| What is the color of the telephone?                            |               |               |               |   |                                   |                                   |
| What is the material of the stool?                             |               |               |               |   |                                   |                                   |


Figure 5. Visualization of the Effects of Different Modules in MRD. Upper: Visualization of the Effects of the Multi-resolution Semantic Fusion Method. Lower: Visualization of the Effects of the Multi-resolution Semantic Fusion Method

## 5.1. Main Results

As shown in Table 1, compared with both the baseline MLLMs and previous baseline approaches, our proposed




MRD framework consistently delivers substantial performance gains across all sub-tasks, datasets, and model configurations. The improvement is most pronounced on the V* dataset using the LaVA-v1.5-7B model, where MRD achieves a remarkable 46.9% absolute increase in accuracy—nearly doubling the original performance. Significant gains are also observed on HR-Bench 4K and HR-Bench 8K, with maximum improvements of 23.6% and 22.8%, respectively.

In comparison to the state-of-the-art baseline RAP, MRD achieves superior performance across all datasets and model settings, yielding an average improvement of 2.8%. When examining results across sub-task categories, MRD demonstrates particularly strong performance on single-object tasks. We attribute this advantage to the integration of a detection module, which provides more accurate localization for isolated objects.

Overall, these results indicate that MRD markedly enhances the perception and understanding capabilities of MLLMs when operating on high-resolution images.

## 5.2. Effect of the Multi-resolution Semantic Fusion

Multi-resolution Semantic Fusion can obtain more accurate information by integrating semantic similarity maps from different resolutions. From the two cases shown in the upper part of Figure 5, we can clearly observe that incorporating multi-resolution semantic fusion allows the high-resolution semantic similarity map to correct the low-resolution map, alleviating semantic deviations caused by different parts of the target object being split across multiple patches. This helps better preserve the integrity of the target object. The results in the cases demonstrate that the approach is effective for both single-object and multi-object tasks. Overall, the experimental results indicate that Multi-resolution Semantic Fusion provides better adaptability to objects of different sizes compared to using a single resolution.

## 5.3. Effect of Open-vocabulary Object Detection

To achieve more accurate and direct localization of the target object at a global scale, we introduce an open-set object detection model. As shown in lower part of Figure 5, sliding-window detection results effectively identify the target object's location. By combining the detection results with semantic similarity scores, MRD amplifies the scores of patches that contain the target object while suppressing false-positive patches that also exhibit high semantic similarity. This integration facilitates a more efficient and accurate patch retrieval process in subsequent searching.

## 5.4. Ablation Study

To better understand the contributions of different modules in our *MRD* framework, we conduct ablation studies

Table 2. Ablation study of different module in *MRD*.

|                   | V\* Bench<br/>Attribute | V\* Bench<br/>Spatial | V\* Bench<br/>Overall | ∆↑   |
| ----------------- | ----------------------- | --------------------- | --------------------- | ---- |
| RAP               | 80.0                    | 84.2                  | 83.6                  | -    |
| OVD               | 84.3                    | 81.6                  | 84.9                  | +1.3 |
| RAP+Multi-res     | 82.9                    | 85.2                  | 85.8                  | +2.2 |
| RAP+OVD           | 85.2                    | 84.2                  | 86.2                  | +2.6 |
| RAP+OVD+Multi-Res | 90.4                    | 85.5                  | 89.3                  | +5.7 |


on the V* dataset using the LLaVA-ov-0.5B model. As shown in Table 2, using the OVD model alone (second row) yields higher localization accuracy for single-object tasks, but its performance on multi-object tasks is inferior to RAP. When RAP employs multi-resolution semantic fusion (third row), performance improves on both single-object and multi-object tasks, indicating that multi-resolution semantic fusion can better handle objects of varying sizes across different scenarios.

Fusing the semantic similarity map obtained from RAP with the detection confidence map from OVD (fourth row) significantly improves performance on single-object tasks; however, the performance on multi-object tasks is even worse than using OVD alone, suggesting that some target objects may be lost during the search. By further incorporating multi-resolution semantic fusion, performance improves on both single-object and multi-object tasks, demonstrating the effectiveness of this fusion strategy.

In summary, introducing OVD helps localize single objects more accurately but may result in missed objects in multi-object scenarios. Multi-resolution semantic fusion corrects semantic similarity scores and preserves object completeness under different conditions, enhancing MLLM performance on both single- and multi-object tasks. The final model, which integrates all modules, achieves a 5.7% higher accuracy than RAP, demonstrating the effectiveness of MRD's design in improving high-resolution image understanding for MLLMs.

## 6. Conclusion

In this work, we propose a novel training-free method, Multi-resolution Retrieval-Detection (MRD), to enhance the understanding of high-resolution images by MLLMs. MRD employs multi-resolution semantic similarity to correct single-resolution similarity maps, ensuring the integrity of target objects. Moreover, to localize target objects more accurately and directly, we introduce an OVD model that identifies object regions using a sliding-window approach. We demonstrate the effectiveness of MRD across multiple high-resolution benchmarks with different MLLMs, showing its superior performance in HR image understanding.




## References

[1] Jinze Bai, Shuai Bai, Yunfei Chu, Zeyu Cui, Kai Dang, Xiaodong Deng, Yang Fan, Wenbin Ge, Yu Han, Fei Huang, et al. Qwen technical report. *arXiv preprint arXiv:2309.16609*, 2023. 1

[2] Jinze Bai, Shuai Bai, Shusheng Yang, Shijie Wang, Sinan Tan, Peng Wang, Junyang Lin, Chang Zhou, and Jingren Zhou. Qwen-vl: A versatile vision-language model for understanding, localization, text reading, and beyond, 2023. 3, 7

[3] Shuai Bai, Keqin Chen, Xuejing Liu, Jialin Wang, Wenbin Ge, Sibo Song, Kai Dang, Peng Wang, Shijie Wang, Jun Tang, et al. Qwen2. 5-vl technical report. *arXiv preprint arXiv:2502.13923*, 2025. 3

[4] Zhe Chen, Weiyun Wang, Yue Cao, Yangzhou Liu, Zhangwei Gao, Erfei Cui, Jinguo Zhu, Shenglong Ye, Hao Tian, Zhaoyang Liu, et al. Expanding performance boundaries of open-source multimodal models with model, data, and test-time scaling. *arXiv preprint arXiv:2412.05271*, 2024. 3

[5] Zhe Chen, Weiyun Wang, Hao Tian, Shenglong Ye, Zhangwei Gao, Erfei Cui, Wenwen Tong, Kongzhi Hu, Jiapeng Luo, Zheng Ma, Ji Ma, Jiaqi Wang, Xiaoyi Dong, Hang Yan, Hewei Guo, Conghui He, Botian Shi, Zhenjiang Jin, Chao Xu, Bin Wang, Xingjian Wei, Wei Li, Wenjian Zhang, Bo Zhang, Pinlong Cai, Licheng Wen, Xiangchao Yan, Min Dou, Lewei Lu, Xizhou Zhu, Tong Lu, Dahua Lin, Yu Qiao, Jifeng Dai, and Wenhai Wang. How far are we to gpt-4v? closing the gap to commercial multimodal models with open-source suites. *Sci. China Inf. Sci.*, 67(12), 2024. 7

[6] Zhe Chen, Jiannan Wu, Wenhai Wang, Weijie Su, Guo Chen, Sen Xing, Muyan Zhong, Qinglong Zhang, Xizhou Zhu, Lewei Lu, et al. Internvl: Scaling up vision foundation models and aligning for generic visual-linguistic tasks. In *Proceedings of the IEEE/CVF conference on computer vision and pattern recognition*, pages 24185–24198, 2024. 3

[7] Shenghao Fu, Qize Yang, Qijie Mo, Junkai Yan, Xihan Wei, Jingke Meng, Xiaohua Xie, and Wei-Shi Zheng. Llmdet: Learning strong open-vocabulary object detectors under the supervision of large language models. In *Proceedings of the Computer Vision and Pattern Recognition Conference*, pages 14987–14997, 2025. 2

[8] Aaron Hurst, Adam Lerer, Adam P Goucher, Adam Perelman, Aditya Ramesh, Aidan Clark, AJ Ostrow, Akila Welihinda, Alan Hayes, Alec Radford, et al. Gpt-4o system card. *arXiv preprint arXiv:2410.21276*, 2024. 7

[9] Bowen Jin, Jinsung Yoon, Jiawei Han, and Sercan O Arik. Long-context llms meet rag: Overcoming challenges for long inputs in rag. *arXiv preprint arXiv:2410.05983*, 2024. 2

[10] Alexander Kirillov, Eric Mintun, Nikhila Ravi, Hanzi Mao, Chloe Rolland, Laura Gustafson, Tete Xiao, Spencer Whitehead, Alexander C Berg, Wan-Yen Lo, et al. Segment anything. In *Proceedings of the IEEE/CVF international conference on computer vision*, pages 4015–4026, 2023. 3

[11] Geng Li, Jinglin Xu, Yunzhen Zhao, and Yuxin Peng. Dyfo: A training-free dynamic focus visual search for enhancing lmms in fine-grained visual understanding. In *Proceedings of the Computer Vision and Pattern Recognition Conference*, pages 9098–9108, 2025. 1, 2, 3

[12] Junnan Li, Dongxu Li, Silvio Savarese, and Steven Hoi. Blip-2: Bootstrapping language-image pre-training with frozen image encoders and large language models. In *International conference on machine learning*, pages 19730–19742. PMLR, 2023. 3

[13] Haotian Liu, Chunyuan Li, Yuheng Li, and Yong Jae Lee. Improved baselines with visual instruction tuning. In *Proceedings of the IEEE/CVF conference on computer vision and pattern recognition*, pages 26296–26306, 2024. 1

[14] Haotian Liu, Chunyuan Li, Yuheng Li, Bo Li, Yuanhan Zhang, Sheng Shen, and Yong Jae Lee. Llavanext: Improved reasoning, ocr, and world knowledge, 2024. 1, 3, 7

[15] Haoyu Lu, Wen Liu, Bo Zhang, Bingxuan Wang, Kai Dong, Bo Liu, Jingxiang Sun, Tongzheng Ren, Zhuoshu Li, Hao Yang, et al. Deepseek-vl: towards real-world vision-language understanding. *arXiv preprint arXiv:2403.05525*, 2024. 3

[16] Gen Luo, Yiyi Zhou, Yuxin Zhang, Xiawu Zheng, Xiaoshuai Sun, and Rongrong Ji. Feast your eyes: Mixture-of-resolution adaptation for multimodal large language models. In *The Thirteenth International Conference on Learning Representations, ICLR 2025, Singapore, April 24-28, 2025*. OpenReview.net, 2025. 7

[17] Alec Radford, Jong Wook Kim, Chris Hallacy, Aditya Ramesh, Gabriel Goh, Sandhini Agarwal, Girish Sastry, Amanda Askell, Pamela Mishkin, Jack Clark, et al. Learning transferable visual models from natural language supervision. In *International conference on machine learning*, pages 8748–8763. PmLR, 2021. 1

[18] Hao Shao, Shengju Qian, Han Xiao, Guanglu Song, Zhuofan Zong, Letian Wang, Yu Liu, and Hongsheng Li. Visual cot: Advancing multi-modal language models with a comprehensive dataset and benchmark for chain-of-thought reasoning. *Advances in Neural Information Processing Systems*, 37:8612–8642, 2024. 1, 3

[19] Haozhan Shen, Kangjia Zhao, Tiancheng Zhao, Ruochen Xu, Zilun Zhang, Mingwei Zhu, and Jianwei Yin. Zoomeye: Enhancing multimodal llms with human-like zooming capabilities through tree-based image exploration. In *Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing*, pages 6613–6629, 2025. 1, 2, 3, 7

[20] Quan Sun, Yuxin Fang, Ledell Wu, Xinlong Wang, and Yue Cao. Eva-clip: Improved training techniques for clip at scale. *arXiv preprint arXiv:2303.15389*, 2023. 1

[21] Wenbin Wang, Liang Ding, Minyan Zeng, Xiabin Zhou, Li Shen, Yong Luo, Wei Yu, and Dacheng Tao. Divide, conquer and combine: A training-free framework for high-resolution image perception in multimodal large language models. In *Proceedings of the AAAI Conference on Artificial Intelligence*, pages 7907–7915, 2025. 1, 2, 3

[22] Wenbin Wang, Yongcheng Jing, Liang Ding, Yingjie Wang, Li Shen, Yong Luo, Bo Du, and Dacheng Tao. Retrieval-augmented perception: High-resolution image perception meets visual rag. *arXiv preprint arXiv:2503.01222*, 2025. 1, 2, 3, 6, 7




[23] Haoran Wei, Lingyu Kong, Jinyue Chen, Liang Zhao, Zheng Ge, Jinrong Yang, Jianjian Sun, Chunrui Han, and Xiangyu Zhang. Vary: Scaling up the vision vocabulary for large vision-language model. In *European Conference on Computer Vision*, pages 408–424. Springer, 2024. 3

[24] Penghao Wu and Saining Xie. V?: Guided visual search as a core mechanism in multimodal llms. In *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, pages 13084–13094, 2024. 1, 2, 3, 6

[25] Shukang Yin, Chaoyou Fu, Sirui Zhao, Ke Li, Xing Sun, Tong Xu, and Enhong Chen. A survey on multimodal large language models. *National Science Review*, 11(12): nwae403, 2024. 1, 3

[26] Alex Young, Bei Chen, Chao Li, Chengen Huang, Ge Zhang, Guanwei Zhang, Heng Li, Jiangcheng Zhu, Jianqun Chen, Jing Chang, Kaidong Yu, Peng Liu, Qiang Liu, Shawn Yue, Senbin Yang, Shiming Yang, Tao Yu, Wen Xie, Wenhao Huang, Xiaohui Hu, Xiaoyi Ren, Xinyao Niu, Pengcheng Nie, Yuchi Xu, Yudong Liu, Yue Wang, Yuxuan Cai, Zhenyu Gu, Zhiyuan Liu, and Zonghong Dai. Yi: Open foundation models by 01.ai. *CoRR*, abs/2403.04652, 2024. 7

[27] Shi Yu, Chaoyue Tang, Bokai Xu, Junbo Cui, Junhao Ran, Yukun Yan, Zhenghao Liu, Shuo Wang, Xu Han, Zhiyuan Liu, et al. Visrag: Vision-based retrieval-augmented generation on multi-modality documents. *arXiv preprint arXiv:2410.10594*, 2024. 3

[28] Duzhen Zhang, Yahan Yu, Jiahua Dong, Chenxing Li, Dan Su, Chenhui Chu, and Dong Yu. Mm-llms: Recent advances in multimodal large language models. In *Findings of the Association for Computational Linguistics ACL 2024*, pages 12401–12430, 2024. 3

[29] Jiarui Zhang, Mahyar Khayatkhoei, Prateek Chhikara, and Filip Ilievski. Mllms know where to look: Training-free perception of small visual details with multimodal llms. *arXiv preprint arXiv:2502.17422*, 2025. 1, 2

[30] Ziwei Zheng, Michael Yang, Jack Hong, Chenxiao Zhao, Guohai Xu, Le Yang, Chao Shen, and Xing Yu. Deepeyes: Incentivizing" thinking with images" via reinforcement learning. *arXiv preprint arXiv:2505.14362*, 2025. 1, 2, 3

[31] Jinguo Zhu, Weiyun Wang, Zhe Chen, Zhaoyang Liu, Shenglong Ye, Lixin Gu, Hao Tian, Yuchen Duan, Weijie Su, Jie Shao, et al. Internvl3: Exploring advanced training and test-time recipes for open-source multimodal models. *arXiv preprint arXiv:2504.10479*, 2025. 3




# MRD: Multi-resolution Retrieval-Detection Fusion for High-Resolution Image Understanding

## Supplementary Material

## A. Implement Details of MRD

Following [22], given an input HR image I, it is first partitioned into smaller image crops based on a predefined crop size, which corresponds to the preferred resolution of the retriver. According to the Resolution of HR image, we set the crop resolutions as 112, 224 and 448 for V* Bench, HR-Bench-4K and HR-Bench-8K respectively. For multi-resolution semantic fusion, the ratio between the high and low resolutions is set to k = 2 in all experiments. For Sliding Window detection, we set window size and step as 1232 and 896 for V* Bench, 2240 and 1792 for HR-Bench-4K, 3136 and 2688 for for HR-Bench-8K to balance efficiency and accuracy. The weight w of the detection confidence map is 0.4 by default in semantic detection map fusion. For the following Retrieved-Exploration Search (RE-Search) process, we adopt the same hyperparameters as the baseline method RAP [22]. In all experiments, the maximum search steps are set to 200, and the answering confidence threshold τ is set to 0.6. In the following hyperparameter studies, all other hyperparameters of our MRD use their default settings unless otherwise specified.

## B. More Experiment Result

To analyze the impact of different hyperparameters on performance, we conduct experiments on MRD using various hyperparameter settings, including Crop Resolution, Maximum Search Steps, Detection Weight, and Detection Window Size. We perform these experiments on the V* Bench using both the LLaVA-ov-0.5B and LLaVA-v1.5-7B models. Unless otherwise specified, all other hyperparameters follow the default settings mentioned in section A.

### B.1. Effect of Crop Resolution

In our experiments, we evaluate the effect of different crop resolutions on performance. The results are shown in Figure 6. For the Single Instance Task (Figure 6 (a)), we observe that MRD remains highly stable across different resolutions for both models, with only minor performance fluctuations, whereas RAP exhibits much larger variations, especially when using LLaVA-ov-0.5B.

For the Cross Instance Task, the performance gap between MRD and RAP is relatively small when using LLaVA-v1.5-7B. However, with LLaVA-ov-0.5B, MRD is largely unaffected by resolution changes, further demonstrating its robustness. Overall, MRD consistently outperforms RAP across different resolutions and model settings, highlighting the advantages of our approach.

In summary, the Multi-resolution Semantic Fusion and Detector Enhancement modules in MRD effectively mitigate the interference caused by fragmenting complete objects across multiple crops when using different crop resolutions. As a result, our MRD performance is only weakly influenced by crop resolution and achieves notably better results in the Single Instance Task.

### B.2. Effect of Maximum Search Steps

The performance of MRD and RAP under different maximum search steps is shown in Figure 7. In Figure 7 (a), for the single-instance task, MRD consistently outperforms RAP across different max step settings on both the LLaVA-ov-0.5B and LLaVA-v1.5-7B models.

In Figure 7 (b), for the Cross Instance Task, MRD is slightly inferior to RAP only when using LLaVA-v1.5-7B with small max steps. However, as the max step increases, MRD surpasses RAP and maintains better performance. Overall, MRD achieves superior results compared to RAP. Notably, MRD with LLaVA-ov-0.5B performs only marginally lower than RAP with the powerful LLaVA-v1.5-7B model.

Most importantly, MRD reaches its peak performance with a significantly smaller number of maximum search steps (Max Step = 30). This means that in practical applications, MRD can operate effectively with fewer steps, achieving high accuracy while reducing search time and improving efficiency."

### B.3. Effect of Detection Weight

The results of using different detection weights are shown in Figure 8. We observe that relying solely on the semantic similarity map (weight = 0) or solely on the detection map (weight = 1) does not yield optimal performance for either task. In contrast, fusing the two maps leads to better results, demonstrating that the semantic similarity map and detection map provide complementary information.

Overall (Figure 8 (c)), the optimal detection weight varies slightly across models: LLaVA-ov-0.5B achieves its best performance at weight = 0.4, while LLaVA-v1.5-7B performs best at weight = 0.2.

### B.4. Effect of Window Size

As shown in Figure 9, adopting different sliding-window sizes for object detection also affects the results. Except for the Cross Instance Task with LLaVA-ov-0.5B, using a





★ LLaVA-ov-0.5B-MRD ● LLaVA-v1.5-7B-MRD ☆ LLaVA-ov-0.5B-RAP ○ LLaVA-v1.5-7B-RAP

| (a) Single | (b) Cross | (c) Overall |
|------------|-----------|-------------|
| ![Graph with accuracy (%) on y-axis from 75-95, resolution on x-axis (96, 112, 144, 160, 224)] | ![Graph with accuracy (%) on y-axis from 75-95, resolution on x-axis (96, 112, 144, 160, 224)] | ![Graph with accuracy (%) on y-axis from 75-95, resolution on x-axis (96, 112, 144, 160, 224)] |

Figure 6. The effect of the resolution of image crops on model performance. Single and Cross represent the attribute recognition and spatial reasoning in V* Bench. (a) Single-instance Task. (b) Cross-instance Task. (c) Overall Performance.

.

★ LLaVA-ov-0.5B-MRD ● LLaVA-v1.5-7B-MRD ☆ LLaVA-ov-0.5B-RAP ○ LLaVA-v1.5-7B-RAP

| (a) Single | (b) Cross | (c) Overall |
|------------|-----------|-------------|
| ![Graph with accuracy (%) on y-axis from 40-90, Max Step on x-axis (1, 10, 30, 50, 100, 200)] | ![Graph with accuracy (%) on y-axis from 65-95, Max Step on x-axis (1, 10, 30, 50, 100, 200)] | ![Graph with accuracy (%) on y-axis from 50-90, Max Step on x-axis (1, 10, 30, 50, 100, 200)] |

Figure 7. The effect of the maximum search steps of *MRD* and *RAP*.

smaller sliding-window size (Window Size = 896) generally yields better performance. This is because a smaller window reduces background interference unrelated to the target object, leading to more accurate detection results.

However, a smaller window size also means that more windows are required to scan the entire high-resolution image, resulting in increased computational complexity and longer processing time. Therefore, to balance accuracy and efficiency, we select a larger sliding-window size, Window Size = 1232, as the default setting.

## B.5. Compared with Other HR Methods

We compare our *MRD* approach with three high-resolution processing baselines *RAP*, DC² and Zoom Eye. DC² is a training-free framework that improves MLLM comprehension of HR images by dividing them into crops, generating textual descriptions for each region, and aggregating these descriptions to obtain a more complete understanding. Zoom Eye, on the other hand, uses a tree-search strategy to traverse the hierarchical visual structure of an image, enabling efficient identification and extraction of relevant information.

As shown in Table 3, all HR processing methods yield overall performance improvements compared with the baseline. Among them, our *MRD* achieves consistently stronger results across most tasks, demonstrating its clear advantage over existing approaches.





LLaVA-ov-0.5B-MRD LLaVA-v1.5-7B-MRD -- LLaVA-ov-0.5B-RAP -- LLaVA-v1.5-7B-RAP

| \*\*Accuracy(%)\*\* 95.0 92.5 90.0 87.5 85.0 82.5 80.0 0 0.2 0.4 0.6 0.8 1.0 Weight \*\*(a) Single\*\* | \*\*Accuracy(%)\*\* 96 94 92 90 88 86 84 82 80 0 0.2 0.4 0.6 0.8 1.0 Weight \*\*(b) Cross\*\* | \*\*Accuracy(%)\*\* 96 94 92 90 88 86 84 0 0.2 0.4 0.6 0.8 1.0 Weight \*\*(c) Overall\*\* |
| ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |


Figure 8. The effect of the detection weight in *MRD*.

LLaVA-ov-0.5B-MRD LLaVA-v1.5-7B-MRD -- LLaVA-ov-0.5B-RAP -- LLaVA-v1.5-7B-RAP

| \*\*Accuracy(%)\*\* 95.0 92.5 90.0 87.5 85.0 82.5 80.0 896 1120 1232 1456 1568 Window Size \*\*(a) Single\*\* | \*\*Accuracy(%)\*\* 96 94 92 90 88 86 84 82 896 1120 1232 1456 1568 Window Size \*\*(b) Cross\*\* | \*\*Accuracy(%)\*\* 96 94 92 90 88 86 84 896 1120 1232 1456 1568 Window Size \*\*(c) Overall\*\* |
| ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |


Figure 9. The effect of the detection window size in *MRD*.

Table 3. Comparison of *MRD* with existing works on high-resolution benchmarks. We conduct experiments on *V*<sup>*</sup> *Bench* and *HR-Bench* using LLaVA-v1.5 7B.

| Method           |      |      |      |      |      |      |      |      |      | Δ(↑)  |
| ---------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ----- |
| LLaVA-v1.5-7B    | 43.5 | 56.6 | 48.7 | 38.5 | 33.8 | 36.1 | 33.0 | 31.3 | 32.1 | -     |
| -w/ *DC*2        | 49.6 | 59.2 | 51.6 | 45.3 | 37.0 | 41.1 | 36.5 | 33.3 | 34.9 | +3.5  |
| -w/ *Zoom Eye*   | 83.5 | 82.9 | 83.3 | 67.8 | 38.8 | 53.3 | 65.5 | 36.0 | 50.8 | +23.5 |
| -w/ *RAP*        | 90.4 | 96.1 | 91.1 | 73.8 | 40.5 | 57.1 | 72.3 | 35.3 | 53.8 | +28.4 |
| -w/ *MRD* (ours) | 97.4 | 96.1 | 95.6 | 76.8 | 42.7 | 59.7 | 72.6 | 37.2 | 54.9 | +31.1 |


## C. Case Study

### C.1. Single-instance Perception Task Examples

Figure 10 shows two single-instance perception cases from each HR benchmarks using *RAP* and *MRD* on LLaVA-v1.5-7B. From the first to the last column, we show: the HR image, the *RAP* semantic similarity map, the object detection confidence map, the *MRD* semantic–detection fusion map, the *RAP* result and the *MRD* result. From the




visualization of *RAP* semantic similarity maps, we can observe that due to the crop partitioning, a complete object may be divided across multiple crops, leading to inconsistencies in semantic similarity among different parts of the object. This inconsistency interferes with the subsequent retrieval process. For example, in the second case of *HR-Bench4K*, *RAP* only retrieves the right half of the speed-limit sign, resulting in an incorrect final prediction. In addition, the semantic similarity maps contain many false positives; for instance, in the first case of *HR-Bench8K*, the sky region—irrelevant to the query—shows undesirably high similarity scores.

*MRD* addresses these issues by using multi-resolution semantic fusion to correct the semantic inconsistencies across different parts of the object, ensuring its completeness. Moreover, by incorporating an object detection model to directly localize the target, *MRD* reinforces the similarity of the true target region while suppressing false positives. As shown in the figure, the *MRD* semantic–detection fusion map exhibits much clearer contrast between the target and irrelevant regions compared with *RAP*, significantly reducing false positives and enabling more accurate retrieval of the target-related crops during the search process.

## C.2. Cross-instance Perception Task Examples

Figure 11 shows two cross-instance perception cases from each HR benchmarks using *RAP* and *MRD* on LLaVA-v1.5-7B. In the cross-instance task, the retrieval results show that *RAP* often retains only a subset of the target objects while ignoring others when multiple objects need to be localized. For example, in the first case of *V* * *Bench*, *RAP* completely misses the pink umbrella. This omission becomes more pronounced when there is a large size discrepancy between different target objects. As seen in the second case of *V* * *Bench* and the two cases from *HRBench-8K*, *RAP* tends to keep only the larger primary object while neglecting the smaller ones. Similar issues also appear in counting scenarios (e.g., the two cases in *HRBench-4K*), where *RAP* identifies only a few among multiple instances.

In contrast, *MRD* leverages object detection to simultaneously detect all target objects, ensuring that even small objects are preserved to the greatest extent. This gives *MRD* a clear advantage in cross-instance perception tasks.





|                                                                              | HR Image                 | RAP Sim Map           | Det Conf Map           | MRD Fusion Map           | RAP Result           | MRD Result           |
| ---------------------------------------------------------------------------- | ------------------------ | --------------------- | ---------------------- | ------------------------ | -------------------- | -------------------- |
| V² Bench                                                                     | ![](street_scene.jpg)    | ![](rap_sim_map1.jpg) | ![](det_conf_map1.jpg) | ![](mrd_fusion_map1.jpg) | ![](rap_result1.jpg) | ![](mrd_result1.jpg) |
| Query: What is the color of the **helmet**?                                  |                          |                       |                        | *White* ✘                |                      | *Green* ✔            |
| V² Bench                                                                     | ![](building_facade.jpg) | ![](rap_sim_map2.jpg) | ![](det_conf_map2.jpg) | ![](mrd_fusion_map2.jpg) | ![](rap_result2.jpg) | ![](mrd_result2.jpg) |
| Query: What is the color of the **hat**?                                     |                          |                       |                        | *Black* ✘                |                      | *White* ✔            |
| HR-Bench-4K                                                                  | ![](dining_room.jpg)     | ![](rap_sim_map3.jpg) | ![](det_conf_map3.jpg) | ![](mrd_fusion_map3.jpg) | ![](rap_result3.jpg) | ![](mrd_result3.jpg) |
| Query: What's the color of the **uniform** of the **figurine on the shelf**? |                          |                       |                        | *Brown* ✘                |                      | *White* ✔            |
| HR-Bench-4K                                                                  | ![](cathedral.jpg)       | ![](rap_sim_map4.jpg) | ![](det_conf_map4.jpg) | ![](mrd_fusion_map4.jpg) | ![](rap_result4.jpg) | ![](mrd_result4.jpg) |
| Query: What is the speed limit indicated on the **sign** in the image?       |                          |                       |                        | *20 km/h* ✘              |                      | *30 km/h* ✔          |
| HR-Bench-8K                                                                  | ![](landscape.jpg)       | ![](rap_sim_map5.jpg) | ![](det_conf_map5.jpg) | ![](mrd_fusion_map5.jpg) | ![](rap_result5.jpg) | ![](mrd_result5.jpg) |
| Query: What's the primary color of the **person's clothing** in the image?   |                          |                       |                        | *White* ✘                |                      | *Blue* ✔             |
| HR-Bench-8K                                                                  | ![](cityscape.jpg)       | ![](rap_sim_map6.jpg) | ![](det_conf_map6.jpg) | ![](mrd_fusion_map6.jpg) | ![](rap_result6.jpg) | ![](mrd_result6.jpg) |
| Query: What's the color of the **trailer**?                                  |                          |                       |                        | *White* ✘                |                      | *Orange* ✔           |


Figure 10. Qualitative examples of **Single-instance Perception** task. We conduct experiments using LLaVA-v1.5-7B on three HR Benchmarks.





|                                                                                           | HR Image                                                                          | RAP Sim Map        | Det Conf Map        | MRD Fusion Map        | RAP Result                                           | MRD Result                                              |
| ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------ | ------------------- | --------------------- | ---------------------------------------------------- | ------------------------------------------------------- |
| V\* Bench                                                                                 | ![](beach_scene)                                                                  | ![](rap_sim_map_1) | ![](det_conf_map_1) | ![](mrd_fusion_map_1) | ![](rap_result_1)<br/>right side ✗                   | ![](mrd_result_1)<br/>left side ✓                       |
|                                                                                           | **Query: Is the yellow umbrella on the left or right side of the pink umbrella?** |                    |                     |                       |                                                      |                                                         |
|                                                                                           | ![](tower_scene)                                                                  | ![](rap_sim_map_2) | ![](det_conf_map_2) | ![](mrd_fusion_map_2) | ![](rap_result_2)<br/>right side ✗                   | ![](mrd_result_2)<br/>left side ✓                       |
| **Query: Is the dog on the left or right side of the golden tower?**                      |                                                                                   |                    |                     |                       |                                                      |                                                         |
| HR-Bench-kK                                                                               | ![](hallway_scene)                                                                | ![](rap_sim_map_3) | ![](det_conf_map_3) | ![](mrd_fusion_map_3) | ![](rap_result_3)<br/>One ✗                          | ![](mrd_result_3)<br/>Two ✓                             |
|                                                                                           | **Query: How many chairs are there in the image?**                                |                    |                     |                       |                                                      |                                                         |
|                                                                                           | ![](sailboat_scene)                                                               | ![](rap_sim_map_4) | ![](det_conf_map_4) | ![](mrd_fusion_map_4) | ![](rap_result_4)<br/>Two ✗                          | ![](mrd_result_4)<br/>Four ✓                            |
| **Query: How many people are there in the boat?**                                         |                                                                                   |                    |                     |                       |                                                      |                                                         |
| HR-Bench-8K                                                                               | ![](albert_hall_scene)                                                            | ![](rap_sim_map_5) | ![](det_conf_map_5) | ![](mrd_fusion_map_5) | ![](rap_result_5)<br/>Behind the bus ✗               | ![](mrd_result_5)<br/>To the left of the bus ✓          |
|                                                                                           | **Query: What is the position of the Royal Albert Hall relative to the bus?**     |                    |                     |                       |                                                      |                                                         |
|                                                                                           | ![](building_scene)                                                               | ![](rap_sim_map_6) | ![](det_conf_map_6) | ![](mrd_fusion_map_6) | ![](rap_result_6)<br/>In front of<br/>the building ✗ | ![](mrd_result_6)<br/>To the left of<br/>the building ✓ |
| **Query: What is the position of the car relative to the central tower of the building?** |                                                                                   |                    |                     |                       |                                                      |                                                         |


Figure 11. Qualitative examples of *Cross-instance Perception* task.We conduct experiments using LLaVA-v1.5-7B on three HR Benchmarks.