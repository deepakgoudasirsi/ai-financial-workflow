import { Router } from "express";
import { z } from "zod";
import { TransactionModel } from "../models/Transaction";
import { analyzeTransactionRisk } from "../services/riskService";

const router = Router();

const CreateTransactionSchema = z.object({
  workflowId: z.string().optional(),
  sourceAccount: z.string(),
  destinationAccount: z.string(),
  amount: z.number().positive(),
  currency: z.string().default("USD"),
  type: z.string(),
  metadata: z.record(z.unknown()).optional()
});

router.get("/", async (req, res) => {
  try {
    const { limit = "50", status } = req.query;
    const query: Record<string, unknown> = {};
    if (status && typeof status === "string") {
      query.status = status;
    }

    const items = await TransactionModel.find(query)
      .sort({ createdAt: -1 })
      .limit(Number(limit));

    res.json(items);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to list transactions" });
  }
});

router.post("/", async (req, res) => {
  try {
    const parsed = CreateTransactionSchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: "Invalid payload", details: parsed.error.flatten() });
    }

    const risk = await analyzeTransactionRisk(parsed.data);

    const tx = await TransactionModel.create({
      ...parsed.data,
      status: risk.riskLevel === "CRITICAL" || risk.riskLevel === "HIGH" ? "FLAGGED" : "APPROVED",
      riskScore: risk.riskScore,
      riskLevel: risk.riskLevel,
      anomalies: risk.anomalies
    });

    res.status(201).json({ transaction: tx, risk });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to create transaction" });
  }
});

router.get("/:id", async (req, res) => {
  try {
    const tx = await TransactionModel.findById(req.params.id);
    if (!tx) {
      return res.status(404).json({ error: "Transaction not found" });
    }
    res.json(tx);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to fetch transaction" });
  }
});

export const transactionRouter = router;

