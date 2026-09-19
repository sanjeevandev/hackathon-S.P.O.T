from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class BoundingBoxItem(BaseModel):
  model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

  box_id: str
  bbox: List[int] = Field(description="[x1, y1, x2, y2] bounding box coordinates in pixels")
  confidence: float = Field(description="Object detection confidence (0-1.0)")
  class_label: str = Field(default="grade_a", alias="class", description="grade_a, urs_onion, damaged, rotten, sprouted, or undersized")
  diameter_mm: float = Field(description="Estimated onion diameter in millimeters")

class DefectFlags(BaseModel):
  damaged: bool = Field(description="Flagged for surface mechanical damage or cracks")
  damaged_count: int = Field(default=0, description="Count of damaged onions")
  rotten: bool = Field(description="Flagged for moisture rot or fungal decay")
  rotten_count: int = Field(default=0, description="Count of rotten onions")
  sprouted: bool = Field(description="Flagged for neck sprouting")
  sprouted_count: int = Field(default=0, description="Count of sprouted onions")
  undersized: bool = Field(description="Flagged for size below 40mm diameter threshold")
  undersized_count: int = Field(default=0, description="Count of undersized onions")

class WeightDistribution(BaseModel):
  total_batch_weight_kg: float = Field(default=100.0, description="Total batch sample weight in KG")
  grade_a_weight_kg: float = Field(description="Weight in KG meeting Grade-A criteria")
  grade_urs_weight_kg: float = Field(description="Weight in KG meeting Grade-URS (Under Relaxed Specifications)")
  rejected_weight_kg: float = Field(description="Weight in KG rejected due to rot/sprouting")
  grade_a_weight_percentage: float = Field(description="Weight percentage for Grade-A")
  grade_urs_weight_percentage: float = Field(description="Weight percentage for Grade-URS")
  rejected_weight_percentage: float = Field(description="Weight percentage for Rejected onions")

class OnionAnalysisResponse(BaseModel):
  analysis_id: str
  batch_id: str = Field(description="Unique batch ID logged in SQLite database")
  center_id: str = Field(description="Procurement Center ID")
  filename: str
  overall_grade: str = Field(description="Grade-A, Grade-URS, or Grade-C (Rejected)")
  confidence_score: float = Field(description="AI vision model confidence score (0-100%)")
  grade_a_percentage: float = Field(description="Percentage of onions classified as Grade-A")
  grade_urs_percentage: float = Field(description="Percentage of onions classified as Grade-URS")
  rejected_percentage: float = Field(description="Percentage of rejected defective onions")
  defect_flags: DefectFlags
  weight_distribution: WeightDistribution
  bounding_boxes: Optional[List[BoundingBoxItem]] = None
  moisture_level: str
  firmness_rating: str
  shelf_life_days: int
  farmer_recommendation: str
  timestamp: str
  sha256_hash: Optional[str] = Field(default=None, description="SHA-256 tamper-evident payload hash")
