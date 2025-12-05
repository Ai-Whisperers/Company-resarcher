import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface RateLimitInfo {
  remaining: number;
  limit: number;
  reset: string;
}

interface ProviderLimits {
  provider: string;
  requests: RateLimitInfo;
  tokens?: RateLimitInfo;
}

interface RateLimitsProps {
  limits: ProviderLimits[];
}

export function RateLimits({ limits }: RateLimitsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>API Rate Limits</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {limits.map((limit) => (
          <div key={limit.provider} className="space-y-2">
            <div className="flex justify-between items-center">
              <h4 className="font-semibold text-sm">{limit.provider}</h4>
              <span className="text-xs text-muted-foreground">
                Reset: {new Date(limit.requests.reset).toLocaleTimeString()}
              </span>
            </div>
            
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span>Requests</span>
                <span>{limit.requests.remaining} / {limit.requests.limit}</span>
              </div>
              <Progress value={(limit.requests.remaining / limit.requests.limit) * 100} />
            </div>

            {limit.tokens && (
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span>Tokens</span>
                  <span>{limit.tokens.remaining} / {limit.tokens.limit}</span>
                </div>
                <Progress value={(limit.tokens.remaining / limit.tokens.limit) * 100} />
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
