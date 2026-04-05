import { Component } from "react";
import s from "./ErrorBoundary.module.css";

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className={s.container}>
          <div className={s.icon}>{"\u26a0"}</div>
          <div className={s.title}>MODULE_LOAD_FAILURE</div>
          <div className={s.message}>
            {this.state.error?.message || "An unexpected error occurred"}
          </div>
          <button className={s.retryBtn} onClick={() => { this.setState({ hasError: false, error: null }); }}>
            {"\u21bb"} RETRY
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
