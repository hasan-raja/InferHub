# Proto

Gateway-to-worker gRPC contracts live under `proto/inferhub/v1`.

Phase 3 defines:

- `LLMWorker.Chat`
- `LLMWorker.StreamChat`
- `ASRWorker.Transcribe`
- `TTSWorker.Synthesize`
- `VisionWorker.Analyze`

Worker containers generate Python bindings during Docker build with `grpcio-tools`.
