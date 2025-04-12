import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  LightbulbIcon,
  Settings2Icon,
  BugIcon,
  RotateCcwIcon,
  LoaderIcon,
} from "lucide-react";

interface GameControlsProps {
  onSuggestMove?: () => void;
  onConfigureBoard?: () => void;
  onToggleDebug?: (enabled: boolean) => void;
  onResetGame?: () => void;
  onDifficultyChange?: (level: number) => void;
  isDebugEnabled?: boolean;
  currentTurn?: "user" | "ai";
  gameStatus?: string;
  isConfigureMode?: boolean;
  isSuggestingMove?: boolean;
  difficultyLevel?: number;
}

const GameControls: React.FC<GameControlsProps> = ({
  onSuggestMove = () => {},
  onConfigureBoard = () => {},
  onToggleDebug = () => {},
  onResetGame = () => {},
  onDifficultyChange = () => {},
  isDebugEnabled = false,
  currentTurn = "user",
  gameStatus = "In Progress",
  isConfigureMode = false,
  isSuggestingMove = false,
  difficultyLevel = 4,
}) => {
  const [debugEnabled, setDebugEnabled] = useState(isDebugEnabled);

  const handleToggleDebug = () => {
    const newValue = !debugEnabled;
    setDebugEnabled(newValue);
    onToggleDebug(newValue);
  };

  return (
    <Card className="w-full max-w-md bg-white shadow-md">
      <CardHeader className="pb-2">
        <CardTitle className="text-xl font-bold">Game Controls</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Badge
              variant={currentTurn === "user" ? "default" : "secondary"}
              className="mb-2"
            >
              {currentTurn === "user" ? "Your Turn" : "AI Turn"}
            </Badge>
            <p className="text-sm text-gray-600">{gameStatus}</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={onResetGame}
            className="flex items-center gap-1"
          >
            <RotateCcwIcon className="h-4 w-4" />
            Reset
          </Button>
        </div>

        <div className="grid gap-3">
          <Button
            onClick={onSuggestMove}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700"
            size="lg"
            disabled={
              isSuggestingMove || currentTurn === "ai" || isConfigureMode
            }
          >
            {isSuggestingMove ? (
              <>
                <LoaderIcon className="h-5 w-5 animate-spin" />
                Calculating...
              </>
            ) : (
              <>
                <LightbulbIcon className="h-5 w-5" />
                Suggest Move
              </>
            )}
          </Button>

          <Button
            onClick={onConfigureBoard}
            variant={isConfigureMode ? "destructive" : "outline"}
            className="w-full flex items-center justify-center gap-2"
          >
            <Settings2Icon className="h-4 w-4" />
            {isConfigureMode ? "Exit Configure Mode" : "Configure Board"}
          </Button>

          <div className="space-y-4 pt-2">
            <div className="flex items-center space-x-2">
              <Switch
                id="debug-mode"
                checked={debugEnabled}
                onCheckedChange={handleToggleDebug}
              />
              <Label
                htmlFor="debug-mode"
                className="flex items-center gap-2 cursor-pointer"
              >
                <BugIcon className="h-4 w-4" />
                Debug Information
              </Label>
            </div>

            <div className="space-y-2">
              <Label htmlFor="difficulty" className="text-sm font-medium">
                AI Difficulty: {difficultyLevel}
              </Label>
              <input
                id="difficulty"
                type="range"
                min="1"
                max="8"
                step="1"
                value={difficultyLevel}
                onChange={(e) => onDifficultyChange(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>Easy</span>
                <span>Medium</span>
                <span>Hard</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default GameControls;
