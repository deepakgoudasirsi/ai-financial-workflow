import { Router } from "express";
import { z } from "zod";
import { WorkflowRunModel } from "../models/WorkflowRun";
import { TransactionModel } from "../models/Transaction";

const router = Router();

const CreateWorkflowSchema = z.object({
  name: z.string(),
  steps: z.array(z.string()).min(1)
});

router.get("/", async (_req, res) => {
  try {
    const runs = await WorkflowRunModel.find().sort({ createdAt: -1 }).limit(20);
    res.json(runs);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to list workflows" });
  }
});

router.post("/", async (req, res) => {
  try {
    const parsed = CreateWorkflowSchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: "Invalid payload", details: parsed.error.flatten() });
    }

    const workflow = await WorkflowRunModel.create({
      ...parsed.data,
      status: "RUNNING"
    });

    res.status(201).json(workflow);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to start workflow" });
  }
});

router.get("/:id/summary", async (req, res) => {
  try {
    const workflow = await WorkflowRunModel.findById(req.params.id);
    if (!workflow) {
      return res.status(404).json({ error: "Workflow not found" });
    }

    const { id } = workflow._id;
    const [total, flagged, highRisk] = await Promise.all([
      TransactionModel.countDocuments({ workflowId: id }),
      TransactionModel.countDocuments({ workflowId: id, status: "FLAGGED" }),
      TransactionModel.countDocuments({
        workflowId: id,
        riskLevel: { $in: ["HIGH", "CRITICAL"] }
      })
    ]);

    res.json({
      workflow,
      stats: {
        totalTransactions: total,
        flaggedTransactions: flagged,
        highRiskTransactions: highRisk
      }
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to summarize workflow" });
  }
});

export const workflowRouter = router;

