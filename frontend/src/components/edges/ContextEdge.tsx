import { BaseEdge, type EdgeProps, getBezierPath } from 'reactflow';
import useStore from '../../store';

const ContextEdge = ({
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  source,
  target,
}: EdgeProps) => {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const highlightedPath = useStore((state) => state.highlightedPath);
  const selectedNodeId = useStore((state) => state.selectedNodeId);

  // An edge is highlighted if both its source and target are in the highlighted path
  // AND the target is "below" the source in the path order (which usually implies lineage)
  // For simple checking: if both are in path, it's likely part of the lineage.
  const isHighlighted = highlightedPath.includes(source) && highlightedPath.includes(target);
  const isDimmed = selectedNodeId && !isHighlighted;

  return (
    <>
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          stroke: isHighlighted ? '#135bec' : (isDimmed ? '#334155' : '#475569'),
          strokeWidth: isHighlighted ? 3 : 1.5,
          opacity: isDimmed ? 0.3 : 1,
          transition: 'all 0.3s ease',
          strokeDasharray: isHighlighted ? '5 5' : '0',
          animation: isHighlighted ? 'dashdraw 0.5s linear infinite' : 'none',
        }}
      />
    </>
  );
};

export default ContextEdge;
