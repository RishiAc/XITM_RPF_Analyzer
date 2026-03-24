-- Add company_evidence_chunks column for pre-computed company doc evidence per evaluation
ALTER TABLE "RFP_Evals"
ADD COLUMN IF NOT EXISTS company_evidence_chunks JSONB DEFAULT '[]';
