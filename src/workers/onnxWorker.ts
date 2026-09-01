import { edgeInferenceEngine } from '../utils/onnxInferenceEngine';

self.onmessage = async (e: MessageEvent) => {
  const { action, imageBase64, batchId, centerId } = e.data;

  if (action === 'runInference') {
    try {
      const result = await edgeInferenceEngine.runEdgeInference(imageBase64, batchId, centerId);
      self.postMessage({ status: 'success', result });
    } catch (err: any) {
      self.postMessage({ status: 'error', error: err.message || 'ONNX Web Worker inference failed' });
    }
  }
};
