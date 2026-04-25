"use client";

import React from "react";

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="flex flex-col items-center justify-center min-h-screen px-6">
          <p className="text-4xl mb-4">😵</p>
          <h2 className="text-xl font-bold mb-2">Что-то пошло не так</h2>
          <p className="text-sm opacity-70 mb-6">
            {this.state.error?.message || "Неизвестная ошибка"}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
            }}
            className="btn-primary"
          >
            Попробовать снова
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}