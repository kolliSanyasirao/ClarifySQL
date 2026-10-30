
export default function SplashScreen() {
  return (
    <div className="clarify-splash">
      <div className="splash-glow splash-glow-one" />
      <div className="splash-glow splash-glow-two" />

      <div className="splash-content">
        <div className="splash-orbit">
          <div className="splash-logo">
            <span>C</span>
          </div>
        </div>

        <h1>
          Clarify<span>SQL</span>
        </h1>

        <p>Adaptive Clarification Engine</p>

        <div className="splash-progress">
          <span />
        </div>

        <small>Preparing your SQL workspace...</small>
      </div>
    </div>
  );
}
