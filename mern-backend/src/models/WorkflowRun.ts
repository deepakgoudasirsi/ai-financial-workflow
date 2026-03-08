import mongoose, { Schema, Document } from "mongoose";

export type WorkflowStatus = "RUNNING" | "COMPLETED" | "FAILED";

export interface IWorkflowRun extends Document {
  name: string;
  steps: string[];
  status: WorkflowStatus;
  startedAt: Date;
  finishedAt?: Date;
  stats?: {
    totalTransactions: number;
    flaggedTransactions: number;
    highRiskTransactions: number;
  };
  createdAt: Date;
  updatedAt: Date;
}

const WorkflowRunSchema = new Schema<IWorkflowRun>(
  {
    name: { type: String, required: true },
    steps: [{ type: String, required: true }],
    status: {
      type: String,
      enum: ["RUNNING", "COMPLETED", "FAILED"],
      default: "RUNNING",
      index: true
    },
    startedAt: { type: Date, default: Date.now },
    finishedAt: { type: Date },
    stats: {
      totalTransactions: { type: Number, default: 0 },
      flaggedTransactions: { type: Number, default: 0 },
      highRiskTransactions: { type: Number, default: 0 }
    }
  },
  {
    timestamps: true
  }
);

WorkflowRunSchema.index({ createdAt: -1 });

export const WorkflowRunModel = mongoose.model<IWorkflowRun>(
  "WorkflowRun",
  WorkflowRunSchema
);

