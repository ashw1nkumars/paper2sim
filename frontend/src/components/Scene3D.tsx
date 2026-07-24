import { useEffect, useMemo, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { Line, OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import type { Scene3D as SceneData, Scene3DObject } from "../lib/api";

// Guard against invisible geometry: a near-black color on the dark background is
// unreadable, so fall back to a bright accent when the requested color is too dark.
function safeColor(input: string | undefined, fallback: string): THREE.Color {
  const c = new THREE.Color(input ?? fallback);
  const luminance = 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;
  return luminance < 0.2 ? new THREE.Color(fallback) : c;
}

// Center + scale every object so any scene (a unit cube or a Lorenz attractor)
// fits the same view. Returns the transform for consistent framing.
function useBounds(objects: Scene3DObject[]) {
  return useMemo(() => {
    const box = new THREE.Box3();
    const v = new THREE.Vector3();
    for (const obj of objects) {
      for (const p of obj.points) box.expandByPoint(v.set(p[0], p[1], p[2]));
    }
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const scale = Math.max(size.x, size.y, size.z) / 2 || 1;
    return { center, scale };
  }, [objects]);
}

function PointsObject({
  obj,
  center,
  scale,
}: {
  obj: Scene3DObject;
  center: THREE.Vector3;
  scale: number;
}) {
  const object = useMemo(() => {
    const n = obj.points.length;
    const positions = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      positions[i * 3] = (obj.points[i][0] - center.x) / scale;
      positions[i * 3 + 1] = (obj.points[i][1] - center.y) / scale;
      positions[i * 3 + 2] = (obj.points[i][2] - center.z) / scale;
    }
    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));

    const hasColors = Array.isArray(obj.colors) && obj.colors.length === n;
    if (hasColors) {
      const colors = new Float32Array(n * 3);
      for (let i = 0; i < n; i++) {
        colors[i * 3] = obj.colors![i][0];
        colors[i * 3 + 1] = obj.colors![i][1];
        colors[i * 3 + 2] = obj.colors![i][2];
      }
      geom.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    }

    const material = new THREE.PointsMaterial({
      size: (obj.size ?? 0.02) * 2,
      sizeAttenuation: true,
      vertexColors: hasColors,
      color: hasColors ? new THREE.Color(0xffffff) : safeColor(obj.color, "#f2662f"),
    });
    return new THREE.Points(geom, material);
  }, [obj, center, scale]);

  return <primitive object={object} />;
}

function LineObject({
  obj,
  center,
  scale,
}: {
  obj: Scene3DObject;
  center: THREE.Vector3;
  scale: number;
}) {
  const pts = useMemo(
    () =>
      obj.points.map(
        (p) =>
          [(p[0] - center.x) / scale, (p[1] - center.y) / scale, (p[2] - center.z) / scale] as [
            number,
            number,
            number,
          ],
      ),
    [obj, center, scale],
  );
  return <Line points={pts} color={safeColor(obj.color, "#22d3ee")} lineWidth={1.5} />;
}

function SceneContent({ scene }: { scene: SceneData }) {
  const { center, scale } = useBounds(scene.objects);
  return (
    <>
      <ambientLight intensity={0.7} />
      <pointLight position={[5, 5, 5]} intensity={0.6} />
      <gridHelper args={[6, 12, "#2a3342", "#1b2230"]} position={[0, -1.2, 0]} />
      {scene.objects.map((obj, i) =>
        obj.kind === "line" ? (
          <LineObject key={i} obj={obj} center={center} scale={scale} />
        ) : (
          <PointsObject key={i} obj={obj} center={center} scale={scale} />
        ),
      )}
      <OrbitControls enablePan enableZoom enableRotate makeDefault />
    </>
  );
}

export default function Scene3D({ url }: { url: string }) {
  const [scene, setScene] = useState<SceneData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => active && setScene(data))
      .catch((e) => active && setError(String(e)));
    return () => {
      active = false;
    };
  }, [url]);

  if (error) return <p className="muted">Could not load 3D scene ({error}).</p>;
  if (!scene) return <p className="muted">Loading 3D scene…</p>;

  return (
    <div className="scene3d">
      <Canvas camera={{ position: [2.6, 1.8, 2.6], fov: 50 }} dpr={[1, 2]}>
        <color attach="background" args={["#05070b"]} />
        <SceneContent scene={scene} />
      </Canvas>
      <div className="scene3d-hint">drag to rotate · scroll to zoom · right-drag to pan</div>
      {scene.title && <div className="scene3d-title">{scene.title}</div>}
    </div>
  );
}
