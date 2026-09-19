import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
  componentName?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`[S.P.O.T. ErrorBoundary] Caught error in ${this.props.componentName || 'component'}:`, error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="w-full p-4 bg-white border border-[#E51E3A]/20 rounded-2xl shadow-sm text-[#163A2D] my-3 font-sans">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-xl bg-[#E51E3A]/10 text-[#E51E3A] flex items-center justify-center shrink-0 mt-0.5">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div className="flex-1 space-y-2">
              <div>
                <h4 className="text-xs font-black uppercase text-[#E51E3A]">
                  {this.props.componentName ? `${this.props.componentName} Offline` : 'Component Error'}
                </h4>
                <p className="text-[11px] text-[#163A2D]/80 mt-0.5 font-medium">
                  {this.state.error?.message || 'An unexpected rendering issue occurred. Core application remains active.'}
                </p>
              </div>
              <div className="flex items-center gap-2 pt-1">
                <button
                  onClick={this.handleReset}
                  className="px-3 py-1.5 bg-[#163A2D] text-white text-[11px] font-bold rounded-xl flex items-center gap-1.5 active:scale-95 transition-transform cursor-pointer"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Retry</span>
                </button>
                {window.location.pathname !== '/' && (
                  <button
                    onClick={() => {
                      window.location.href = '/';
                    }}
                    className="px-3 py-1.5 bg-[#F7F1E7] border border-[#163A2D]/20 text-[#163A2D] text-[11px] font-bold rounded-xl flex items-center gap-1.5 active:scale-95 transition-transform cursor-pointer"
                  >
                    <Home className="w-3 h-3" />
                    <span>Return to Home</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
