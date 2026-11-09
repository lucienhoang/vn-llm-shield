# Local LLM setup

- Hardware: AMD Ryzen 7 5700U, 16GB RAM, integrated GPU (CPU inference)
- Runtime: Ollama 0.40.15
- Model: qwen2.5:3b (Q4_K_M)

| Model       | Quantization | Eval rate (tokens/s) | Vietnamese quality (note) |
| ----------- | ------------ | -------------------- | ------------------------- |
| qwen2.5:3b  | Q4_K_M       | 13.82                | Good                      |
| llama3.2:3b |              |                      |                           |

Chosen model: qwen2.5:3b. Reason: .
