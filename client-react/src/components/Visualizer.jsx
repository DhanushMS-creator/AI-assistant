import React, { forwardRef, useImperativeHandle, useRef } from 'react';

const Visualizer = forwardRef(({ state }, ref) => {
    const containerRef = useRef(null);

    useImperativeHandle(ref, () => ({
        updateVolume: (volume) => {
            if (!containerRef.current) return;
            const scale = 1 + (volume / 2);
            const circles = containerRef.current.querySelectorAll('.circle');
            circles.forEach(c => c.style.transform = `scale(${scale})`);
        }
    }));

    return (
        <div ref={containerRef} id="visualizer" className={`visualizer ${state}`}>
            <div className="circle"></div>
            <div className="circle"></div>
            <div className="circle"></div>
        </div>
    );
});

export default Visualizer;
