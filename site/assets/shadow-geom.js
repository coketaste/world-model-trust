/* Side-view geometry for the depth-size ambiguity (pure, node-testable).
   Camera at (0, CAM_H) looking along +z. The occluder sits on a fixed camera ray; moving it along that ray while scaling
   its radius in proportion leaves the camera's image unchanged (the null direction). Its shadow on the floor y=0 does change. */
(function (root) {
  const CAM_H = 1.5, VHALF = 23.4, Z_REF = 3, Y_REF = 1.2, R_REF = 0.35, LIGHT_DIST = 4;
  const DIR = [Z_REF, Y_REF - CAM_H];             // fixed camera ray through the occluder centre
  const Z_VISIBLE = CAM_H / Math.tan(VHALF * Math.PI / 180); // nearest floor the camera can see

  function occluder(z) {
    const k = z / Z_REF;
    return { z: CAM_H * 0 + DIR[0] * k, y: CAM_H + DIR[1] * k, r: R_REF * k, k };
  }
  /* angular half-size of the silhouette, as seen from the camera (should be constant in z) */
  function silhouetteDeg(o) { return Math.asin(o.r / Math.hypot(o.z, o.y - CAM_H)) * 180 / Math.PI; }

  /* light at distance LIGHT_DIST from the occluder, elevation e (deg), side = -1 (camera side) or +1 (behind occluder) */
  function lightPos(o, elevDeg, side) {
    const e = elevDeg * Math.PI / 180;
    return { z: o.z + side * LIGHT_DIST * Math.cos(e), y: o.y + LIGHT_DIST * Math.sin(e) };
  }

  /* floor interval [lo, hi] shadowed by circle o from light L; hi may be Infinity when a tangent ray never reaches the floor */
  function shadow(o, L) {
    const dz = o.z - L.z, dy = o.y - L.y, dist = Math.hypot(dz, dy);
    if (dist <= o.r) return null;
    const base = Math.atan2(dy, dz), half = Math.asin(o.r / dist);
    const hits = [base - half, base + half].map((a) => {
      const sy = Math.sin(a);
      if (sy >= -1e-9) return Infinity;            // ray does not descend
      return L.z + Math.cos(a) * (-L.y / sy);
    });
    return { lo: Math.min(...hits), hi: Math.max(...hits) };
  }
  const center = (s) => (s && isFinite(s.lo) && isFinite(s.hi) ? (s.lo + s.hi) / 2 : null);

  /* how far the shadow moves for a 10% change in depth along the ambiguity (the lever arm that breaks the null) */
  function leverArm(z, elevDeg, side) {
    const a = occluder(z), b = occluder(z * 1.1);
    const ca = center(shadow(a, lightPos(a, elevDeg, side))), cb = center(shadow(b, lightPos(b, elevDeg, side)));
    return ca == null || cb == null ? null : Math.abs(cb - ca);
  }
  /* length of shadow on floor the camera can see (ignores the occluder hiding part of it) */
  function visibleShadow(s) {
    if (!s) return 0;
    const lo = Math.max(s.lo, Z_VISIBLE), hi = s.hi;
    return Math.max(0, hi - lo);
  }

  root.ShadowGeom = { CAM_H, VHALF, Z_VISIBLE, occluder, silhouetteDeg, lightPos, shadow, center, leverArm, visibleShadow };
})(typeof window !== "undefined" ? window : globalThis);
