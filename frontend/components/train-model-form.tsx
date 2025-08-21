"use client"

import type React from "react"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useToast } from "@/hooks/use-toast"
import { Loader2, Play, CheckCircle, AlertCircle, Brain, FileText, Database } from "lucide-react"
import { trainModel, type TrainModelRequest, type TrainModelResponse } from "@/lib/train-api"

interface TrainingStatus {
  isTraining: boolean
  progress: number
  stage: string
  result: TrainModelResponse | null
}

export function TrainModelForm() {
  const [dataPath, setDataPath] = useState("labeled_pairs.csv")
  const [trainingStatus, setTrainingStatus] = useState<TrainingStatus>({
    isTraining: false,
    progress: 0,
    stage: "",
    result: null,
  })
  const { toast } = useToast()

  const simulateTrainingProgress = () => {
    const stages = [
      { stage: "Loading loan applicant data...", progress: 10 },
      { stage: "Preprocessing customer pairs...", progress: 25 },
      { stage: "Initializing neural network...", progress: 40 },
      { stage: "Training duplicate detection model...", progress: 60 },
      { stage: "Validating on test dataset...", progress: 80 },
      { stage: "Optimizing risk thresholds...", progress: 90 },
      { stage: "Deploying updated model...", progress: 100 },
    ]

    let currentStage = 0
    const interval = setInterval(() => {
      if (currentStage < stages.length) {
        setTrainingStatus((prev) => ({
          ...prev,
          progress: stages[currentStage].progress,
          stage: stages[currentStage].stage,
        }))
        currentStage++
      } else {
        clearInterval(interval)
      }
    }, 1500) // Update every 1.5 seconds

    return interval
  }

  const handleSubmit = async (
    e?: React.FormEvent | React.MouseEvent
  ) => {
    e?.preventDefault()

    if (!dataPath.trim()) {
      toast({
        title: "Validation Error",
        description: "Please provide a data file path",
        variant: "destructive",
      })
      return
    }

    setTrainingStatus({
      isTraining: true,
      progress: 0,
      stage: "Initializing model training...",
      result: null,
    })

    // Start progress simulation
    const progressInterval = simulateTrainingProgress()

    try {
      const request: TrainModelRequest = {
        data_path: dataPath,
      }

      const result = await trainModel(request)

      // Clear the progress interval
      clearInterval(progressInterval)

      if (result.success && result.data) {
        setTrainingStatus({
          isTraining: false,
          progress: 100,
          stage: "Model training completed successfully!",
          result: result.data,
        })

        toast({
          title: "Training Complete",
          description: result.data.message || "Loan duplicate detection model updated successfully",
        })
      } else {
        setTrainingStatus({
          isTraining: false,
          progress: 0,
          stage: "Training failed",
          result: null,
        })

        toast({
          title: "Training Failed",
          description: result.message || "Failed to train model",
          variant: "destructive",
        })
      }
    } catch (error) {
      clearInterval(progressInterval)
      setTrainingStatus({
        isTraining: false,
        progress: 0,
        stage: "Training failed",
        result: null,
      })

      toast({
        title: "Error",
        description: "Failed to train model. Please try again.",
        variant: "destructive",
      })
    }
  }

  const resetTraining = () => {
    setTrainingStatus({
      isTraining: false,
      progress: 0,
      stage: "",
      result: null,
    })
  }

  return (
    <div className="space-y-6">
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-primary">
            <Brain className="h-5 w-5" />
            Train Loan Duplicate Detection Model
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* CSV Path Input */}
            <div className="space-y-2">
              <Label htmlFor="data_path">Training Data Path</Label>
              <Input
                id="data_path"
                value={dataPath}
                onChange={(e) => setDataPath(e.target.value)}
                placeholder="labeled_pairs.csv"
                disabled={trainingStatus.isTraining}
                className="font-mono"
              />
              <p className="text-sm text-muted-foreground">
                Path to the data file (CSV, Parquet, or Hugging Face dataset directory) containing labeled loan applicant pairs for training the duplicate detection model
              </p>
            </div>

            {/* Training Progress */}
            {(trainingStatus.isTraining || trainingStatus.result) && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Training Progress</Label>
                    <span className="text-sm text-muted-foreground">{trainingStatus.progress}%</span>
                  </div>
                  <Progress value={trainingStatus.progress} className="w-full" />
                  {trainingStatus.stage && (
                    <p className="text-sm text-muted-foreground flex items-center gap-2">
                      {trainingStatus.isTraining && <Loader2 className="h-4 w-4 animate-spin" />}
                      {trainingStatus.stage}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex gap-4">
              <Button
                type="button"
                onClick={handleSubmit}
                disabled={trainingStatus.isTraining}
                className="bg-secondary text-secondary-foreground hover:bg-secondary/90"
              >
                {trainingStatus.isTraining ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                {trainingStatus.isTraining ? "Training in Progress..." : "Start Training"}
              </Button>

              {(trainingStatus.result || (!trainingStatus.isTraining && trainingStatus.progress > 0)) && (
                <Button type="button" variant="outline" onClick={resetTraining}>
                  Reset
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Training Results */}
      {trainingStatus.result && (
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {trainingStatus.result.success ? (
                <CheckCircle className="h-5 w-5 text-secondary" />
              ) : (
                <AlertCircle className="h-5 w-5 text-destructive" />
              )}
              Training Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Alert className={trainingStatus.result.success ? "border-secondary" : "border-destructive"}>
              <AlertDescription className="space-y-4">
                <div>
                  <strong>Status:</strong> {trainingStatus.result.message}
                </div>

                {trainingStatus.result.details && (
                  <div className="space-y-2">
                    <div className="grid gap-2 md:grid-cols-2 text-sm">
                      {trainingStatus.result.details.pairs_processed && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Applicant Pairs Processed:</span>
                          <span className="font-medium">
                            {trainingStatus.result.details.pairs_processed.toLocaleString()}
                          </span>
                        </div>
                      )}
                      {trainingStatus.result.details.accuracy && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Detection Accuracy:</span>
                          <span className="font-medium">
                            {(trainingStatus.result.details.accuracy * 100).toFixed(2)}%
                          </span>
                        </div>
                      )}
                      {trainingStatus.result.details.training_time && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Training Duration:</span>
                          <span className="font-medium">{trainingStatus.result.details.training_time.toFixed(1)}s</span>
                        </div>
                      )}
                      {trainingStatus.result.training_id && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Model Version:</span>
                          <code className="bg-muted px-2 py-1 rounded text-xs">
                            {trainingStatus.result.training_id}
                          </code>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      )}

      {/* Training Information */}
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-primary">
            <FileText className="h-5 w-5" />
            Loan Applicant Training Guidelines
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 text-sm">
            <div>
              <h4 className="font-medium mb-2 flex items-center gap-2">
                <Database className="h-4 w-4" />
                CSV Format Requirements
              </h4>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>CSV file should contain labeled loan applicant pairs for training</li>
                <li>Each row represents a pair of applicant records with identity and loan information</li>
                <li>Include columns: name, DOB, phone, email, government_id, address, loan_type, amount</li>
                <li>Label column should indicate if the pair represents the same person (1) or different (0)</li>
                <li>Consider loan context: same person applying for multiple loans vs. different applicants</li>
              </ul>
            </div>

            <div>
              <h4 className="font-medium mb-2">Banking-Specific Training Process</h4>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>Model learns to identify duplicate loan applicants across multiple applications</li>
                <li>Analyzes identity patterns while considering legitimate multiple loan scenarios</li>
                <li>Optimizes risk thresholds for banking compliance and fraud prevention</li>
                <li>Validates performance against known duplicate cases and false positives</li>
              </ul>
            </div>

            <div>
              <h4 className="font-medium mb-2">Banking Best Practices</h4>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>Include diverse examples: legitimate multiple loans vs. fraudulent applications</li>
                <li>Account for name variations, address changes, and updated contact information</li>
                <li>Balance dataset with equal examples of duplicates and unique applicants</li>
                <li>Retrain monthly as new applicant patterns and fraud techniques emerge</li>
                <li>Validate against regulatory compliance requirements for loan processing</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
