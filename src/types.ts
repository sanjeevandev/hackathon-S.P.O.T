export type LanguageCode = 'en' | 'hi' | 'ta' | 'mr';

export interface LanguageOption {
  code: LanguageCode;
  name: string;
  nativeName: string;
  flag: string;
  audioText: string;
}

export type AppStep = 'language' | 'camera' | 'results' | 'history' | 'admin' | AppRoute;

export interface BoundingBoxItem {
  box_id: string;
  bbox: [number, number, number, number];
  confidence: number;
  class: string;
  diameter_mm: number;
}

export interface DefectFlagsData {
  damaged: boolean;
  damaged_count: number;
  rotten: boolean;
  rotten_count: number;
  sprouted: boolean;
  sprouted_count: number;
  undersized: boolean;
  undersized_count: number;
}

export interface WeightDistributionData {
  total_batch_weight_kg: number;
  grade_a_weight_kg: number;
  grade_urs_weight_kg: number;
  rejected_weight_kg: number;
  grade_a_weight_percentage: number;
  grade_urs_weight_percentage: number;
  rejected_weight_percentage: number;
}

export interface ScanResult {
  analysisId?: string;
  batchId: string;
  centerId: string;
  grade: 'A' | 'URS' | 'C';
  overallGrade: string;
  qualityTitleKey: string;
  score: number;
  gradeAPercentage: number;
  gradeURSPercentage: number;
  rejectedPercentage: number;
  defectFlags?: DefectFlagsData;
  weightDistribution?: WeightDistributionData;
  boundingBoxes?: BoundingBoxItem[];
  moisture: string;
  firmness: string;
  shelfLife: string;
  defectSummary: string;
  recommendation: string;
  imageUrl: string;
  timestamp: string;
  status?: 'ACCEPTED' | 'DISPUTED';
  sha256Hash?: string;
  isInferenceEdge?: boolean;
  edgeLatencyMs?: number;
  serverLatencyMs?: number;
  benchmarkLog?: string;
  source?: string;
}

export interface PastSessionLog {
  id: number;
  batch_id: string;
  center_id: string;
  timestamp: string;
  filename: string;
  overall_grade: string;
  confidence_score: number;
  grade_a_percentage: number;
  grade_urs_percentage: number;
  rejected_percentage: number;
  damaged_count: number;
  rotten_count: number;
  sprouted_count: number;
  undersized_count: number;
  grade_a_weight_kg: number;
  grade_urs_weight_kg: number;
  rejected_weight_kg: number;
  total_weight_kg: number;
  moisture_level: string;
  firmness_rating: string;
  shelf_life_days: number;
  farmer_recommendation: string;
  status?: 'ACCEPTED' | 'DISPUTED';
  sha256_hash?: string;
}

export interface DistrictMetricSummary {
  district: string;
  centerCount: number;
  totalMT: number;
  gradeAMT: number;
  gradeURSMT: number;
  rejectedMT: number;
  disputeCount: number;
  disputeRatePct: number;
}

export type AppRoute =
  | 'landing'
  | 'home'
  | 'new_inspection'
  | 'capture'
  | 'analyzing'
  | 'result'
  | 'evidence'
  | 'report'
  | 'history'
  | 'history_detail'
  | 'analytics'
  | 'assistant'
  | 'admin'
  | 'internal_annotation'
  | 'splash';

export interface NewInspectionMeta {
  batch_id: string;
  supplier: string;
  procurement_center_id: string;
  declared_weight_kg?: number;
  notes?: string;
  sampling_status: 'SAMPLE_ONLY';
}

export interface EvidenceRegion {
  defect_type: string;
  coordinates: [number, number, number, number];
  confidence: number;
  region_reference?: string;
}

export interface OnionResult {
  onion_id: string;
  bounding_box: [number, number, number, number];
  mask_reference?: string;
  detection_confidence: number;
  defect_probabilities: {
    damage: number;
    rot: number;
    sprouting: number;
  };
  size_estimate: {
    estimated_diameter_mm?: number | null;
    status: 'AVAILABLE' | 'UNAVAILABLE';
    confidence: number;
  };
  evidence_regions: EvidenceRegion[];
  final_status: 'HEALTHY' | 'DAMAGED' | 'ROTTEN' | 'SPROUTED' | 'UNDERSIZED';
}

export interface BatchStatistics {
  total_visible_onions: number;
  total_analyzed_onions: number;
  healthy_count: number;
  damaged_count: number;
  rotten_count: number;
  sprouted_count: number;
  undersized_count: number;
  healthy_percentage: number;
  damaged_percentage: number;
  rotten_percentage: number;
  sprouted_percentage: number;
  undersized_percentage: number;
}

export interface Coverage {
  captured_sample_images_count: number;
  total_visible_onions: number;
  total_analyzed_onions: number;
  sampling_status: 'SAMPLE_ONLY';
  coverage_notes?: string;
}

export interface GradingPresentation {
  quality_score: number;
  prototype_grade: 'Grade-A' | 'Grade-URS' | 'Grade-C';
  grade_a_percent: number;
  urs_percent: number;
  review_status: 'ACCEPTED' | 'REVIEW_REQUIRED';
  review_reason: string[];
  inspection_confidence: number;
  grading_profile_id: string;
  grading_profile_version: string;
}

export interface Explanation {
  headline: string;
  primary_factors: string[];
  supporting_factors: string[];
  review_message?: string | null;
  limitations: string[];
}

export interface ModelInformation {
  model_id: string;
  model_name: string;
  model_version: string;
  source: 'development_mock' | 'real_model';
}

export interface GradingProfileInformation {
  profile_id: string;
  profile_name: string;
  version: string;
  status: string;
  official_status: string;
  disclaimer: string;
}

export interface CanonicalInspectionResult {
  inspection_id: string;
  batch_id: string;
  status: 'COMPLETE' | 'RETAKE_REQUIRED' | 'REVIEW_REQUIRED' | 'MODEL_UNAVAILABLE' | 'FAILED';
  sampling_status: 'SAMPLE_ONLY';
  image_quality: {
    quality_status: 'PASS' | 'RETAKE_REQUIRED';
    metrics?: Record<string, any>;
  };
  coverage: Coverage;
  onions: OnionResult[];
  batch_statistics: BatchStatistics;
  grading?: GradingPresentation | null;
  explanation: Explanation;
  confidence: float;
  review: {
    review_status: string;
    review_reason: string;
  };
  model: ModelInformation;
  grading_profile: GradingProfileInformation;
  report_reference?: string | null;
  captured_image_url?: string;
}

export interface InspectionReport {
  report_id: string;
  report_version: number;
  inspection_id: string;
  batch_id: string;
  generated_at: string;
  batch_metadata: Record<string, any>;
  sampling: Record<string, any>;
  image_quality: Record<string, any>;
  statistics: Record<string, any>;
  grading?: Record<string, any> | null;
  explanation: Record<string, any>;
  model_information: Record<string, any>;
  grading_profile_information: Record<string, any>;
  disclaimer: string;
  limitations: string[];
}

export interface HistoryItem {
  inspection_id: string;
  batch_id: string;
  status: string;
  started_at: string;
  confidence: number;
  review_status: string;
  model_version_id: string;
  grading_result?: {
    grade: string;
    quality_score: number;
    profile_id: string;
    sampling_status: string;
  } | null;
}

export type float = number;
