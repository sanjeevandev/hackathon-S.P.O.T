export type LanguageCode = 'en' | 'hi' | 'ta' | 'mr';

export interface LanguageOption {
  code: LanguageCode;
  name: string;
  nativeName: string;
  flag: string;
  audioText: string;
}

export type AppStep = 'language' | 'camera' | 'results' | 'history' | 'admin';

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
  isInferenceEdge?: boolean;
  edgeLatencyMs?: number;
  serverLatencyMs?: number;
  benchmarkLog?: string;
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

export interface AdminAnalyticsSummary {
  totalInspectedMT: number;
  totalBatchesCount: number;
  overallGradeAPct: number;
  overallURSPct: number;
  overallRejectedPct: number;
  totalDisputeCount: number;
  disputeRatePct: number;
  districtBreakdown: DistrictMetricSummary[];
}
