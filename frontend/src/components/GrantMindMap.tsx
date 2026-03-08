import React, { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { Tldraw, useEditor, Editor, createShapeId } from '@tldraw/tldraw';
import '@tldraw/tldraw/tldraw.css';

// Custom hook to sync store data to tldraw
const MindMapBrain = () => {
    const editor = useEditor();
    const { orgProfile, grants, currentSession, isHunting } = useStore();
    const [isInitialized, setIsInitialized] = useState(false);

    useEffect(() => {
        if (!editor || !orgProfile || isInitialized) return;

        // Clear board
        editor.selectAll().deleteShapes(editor.getSelectedShapeIds());

        // Create central org node
        const orgNodeId = createShapeId('org-root');
        editor.createShape({
            id: orgNodeId,
            type: 'geo',
            x: 400,
            y: 300,
            props: {
                geo: 'ellipse',
                w: 200,
                h: 100,
                text: orgProfile.name,
                color: 'light-blue',
                fill: 'solid',
                size: 'l'
            }
        });

        // Create category nodes
        const categories = Array.isArray(orgProfile.focus_areas)
            ? orgProfile.focus_areas
            : (orgProfile.focus_areas as string).split(',').map((s: string) => s.trim());

        categories.forEach((cat, index) => {
            const angle = (index / categories.length) * Math.PI * 2;
            const radius = 250;
            const cx = 400 + 100 + Math.cos(angle) * radius;
            const cy = 300 + 50 + Math.sin(angle) * radius;

            const catNodeId = createShapeId(`cat-${index}`);
            editor.createShape({
                id: catNodeId,
                type: 'geo',
                x: cx - 75,
                y: cy - 35,
                props: {
                    geo: 'rectangle',
                    w: 150,
                    h: 70,
                    text: cat,
                    color: 'light-green',
                    fill: 'solid',
                    size: 'm'
                }
            });

            // Arrow from core to category
            editor.createShape({
                id: createShapeId(),
                type: 'arrow',
                props: {
                    start: { x: 500, y: 350 }, // rough center of ellipse
                    end: { x: cx, y: cy },
                    color: 'light-green',
                    size: 'm'
                }
            });
        });

        setIsInitialized(true);
        editor.zoomToFit({ duration: 500, padding: 50 });
    }, [editor, orgProfile, isInitialized]);

    // Sync Grants to Map
    useEffect(() => {
        if (!editor || grants.length === 0) return;

        grants.forEach((grant, i) => {
            const shapeId = createShapeId(`grant-${grant.id}`);

            // Check if already drawn
            if (editor.getShape(shapeId)) return;

            // Draw branching outwards
            const angle = Math.random() * Math.PI * 2;
            const radius = 450 + (i * 10);
            const cx = 500 + Math.cos(angle) * radius;
            const cy = 350 + Math.sin(angle) * radius;

            editor.createShape({
                id: shapeId,
                type: 'geo',
                x: cx - 100,
                y: cy - 40,
                props: {
                    geo: 'rectangle',
                    w: 200,
                    h: 80,
                    text: grant.title.substring(0, 30) + '...',
                    color: grant.match_score > 80 ? 'light-violet' : 'yellow',
                    fill: 'solid',
                    size: 's'
                }
            });

            // Link it to the center or a random category for visual flair
            editor.createShape({
                id: createShapeId(),
                type: 'arrow',
                props: {
                    start: { x: 500, y: 350 },
                    end: { x: cx, y: cy },
                    color: 'grey',
                    dash: 'dashed'
                }
            });
        });

        if (isHunting) {
            editor.zoomToFit({ duration: 1000, padding: 100 });
        }
    }, [editor, grants, isHunting]);

    return null;
};

const GrantMindMap = () => {
    return (
        <div className="w-full h-full relative rounded-2xl overflow-hidden border border-white/10 bg-[#0a0f1e] shadow-2xl">
            {/* Background radial gradient specifically for the canvas area */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(99,102,241,0.05)_0%,transparent_100%)] pointer-events-none"></div>

            <Tldraw
                inferDarkMode
                className="tl-theme__dark"
                options={{ maxPages: 1 }}
            >
                <MindMapBrain />
            </Tldraw>

            <div className="absolute bottom-4 left-4 glass-panel px-3 py-1.5 text-xs text-slate-400 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse"></span>
                AetherForge Weave Mesh Active
            </div>
        </div>
    );
};

export default GrantMindMap;
