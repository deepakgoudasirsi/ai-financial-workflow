import { OpenAI } from "openai";
import { z } from "zod";
import { config } from "../config";
import { ITransaction } from "../models/Transaction";

const RiskAnalysisSchema = z.object({
  riskScore: z.number().min(0).max(1),
  riskLevel: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
  anomalies: z.array(z.string()).default([]),
  rationale: z.string().optional()
});

export type RiskAnalysis = z.infer<typeof RiskAnalysisSchema>;

const openai = config.openAiApiKey
  ? new OpenAI({ apiKey: config.openAiApiKey })
  : null;

export async function analyzeTransactionRisk(
  tx: Pick<
    ITransaction,
    | "sourceAccount"
    | "destinationAccount"
    | "amount"
    | "currency"
    | "type"
    | "metadata"
  >
): Promise<RiskAnalysis> {
  if (!openai) {
    // Safe fallback when OpenAI is not configured
    const heuristicScore = Math.min(tx.amount / 10000, 1);
    return {
      riskScore: heuristicScore,
      riskLevel:
        heuristicScore > 0.8
          ? "CRITICAL"
          : heuristicScore > 0.6
          ? "HIGH"
          : heuristicScore > 0.3
          ? "MEDIUM"
          : "LOW",
      anomalies: heuristicScore > 0.8 ? ["amount_unusually_high"] : [],
      rationale: "Heuristic risk scoring used because OpenAI API is not configured."
    };
  }

  const prompt = `
You are a risk engine for a financial institution. 
Given a single transaction, return a concise JSON object with:
- riskScore: number between 0 and 1
- riskLevel: one of LOW, MEDIUM, HIGH, CRITICAL
- anomalies: short list of anomaly reason strings
- rationale: short human-readable explanation.

Transaction JSON:
${JSON.stringify(tx, null, 2)}

Respond with JSON only.`;

  const response = await openai.responses.create({
    model: config.openAiModel,
    input: prompt,
    response_format: { type: "json_object" }
  });

  const json =
    (response.output[0].content[0]?.type === "output_text" &&
      safeJsonParse(response.output[0].content[0].text)) ||
    {};

  const parsed = RiskAnalysisSchema.safeParse(json);
  if (!parsed.success) {
    throw new Error("Failed to parse risk analysis from OpenAI response");
  }

  return parsed.data;
}

function safeJsonParse(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return {};
  }
}

