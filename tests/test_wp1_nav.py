import numpy as np

from wmt import wp1_nav as nav


def test_dijkstra_open_grid_is_octile():
    free = np.ones((nav.N, nav.N), bool)
    dist, parent = nav.dijkstra(free)
    s = nav.START
    g = (s[0] + 5, s[1] + 3)
    assert abs(dist[g] - (3 * nav.SQRT2 + 2)) < 1e-9
    path = nav.extract_path(parent, g, free.shape)
    assert path[0] == s and path[-1] == g
    assert abs(nav.path_length(path) - (3 * nav.SQRT2 + 2) * nav.CELL) < 1e-9


def test_dijkstra_detours_around_wall_and_no_corner_cutting():
    free = np.ones((nav.N, nav.N), bool)
    s = nav.START
    free[s[0] + 2, s[1] - 10:s[1] + 10] = False  # wall in front, gap only beyond +/-10
    dist, _ = nav.dijkstra(free)
    assert dist[s[0] + 4, s[1]] > 4 + 15
    free2 = np.ones((nav.N, nav.N), bool)
    free2[s[0] + 1, s[1]] = False
    free2[s[0], s[1] + 1] = False
    dist2, _ = nav.dijkstra(free2)
    assert dist2[s[0] + 1, s[1] + 1] > nav.SQRT2 + 1  # direct diagonal squeeze between two blocked cells is forbidden


def _toy_world():
    # floor at y=1 (y down), obstacle box between x in [1,1.4], z in [0,0.4], height 0.5 above the floor
    xs, zs = np.meshgrid(np.arange(-2, 2, 0.05), np.arange(-2, 2, 0.05))
    floor = np.column_stack([xs.ravel(), np.full(xs.size, 1.0), zs.ravel()])
    bx, bz = np.meshgrid(np.arange(1.0, 1.4, 0.05), np.arange(0.0, 0.4, 0.05))
    box = np.column_stack([bx.ravel(), np.full(bx.size, 0.5), bz.ravel()])
    return np.vstack([floor, box, box + [0, 0.01, 0]])


def test_floor_height_and_grids_on_toy_scene():
    P = _toy_world()
    # histogram mode is the floor slab (the sparse box is not the mode)
    assert abs(nav.floor_height(P) - 1.0) < 0.05
    fl = nav.floor_grid(P, 1.0)
    ob = nav.obstacle_grid(P, 1.0)
    ix, iz = int((1.2 + nav.HALF) / nav.CELL), int((0.2 + nav.HALF) / nav.CELL)
    assert ob[ix, iz] and fl[ix, iz]  # box sits on the floor
    assert not ob[int((-1 + nav.HALF) / nav.CELL), int((-1 + nav.HALF) / nav.CELL)]
    assert not fl[int((4 + nav.HALF) / nav.CELL), int((4 + nav.HALF) / nav.CELL)]  # off the floor patch: no floor
    assert nav.inflate(ob)[ix + 1, iz] and not ob[ix + 4, iz + 4]


def test_execute_reports_collision_and_fall():
    floor = np.ones((nav.N, nav.N), bool)
    obst = np.zeros_like(floor)
    s = nav.START
    path = [s, (s[0] + 1, s[1]), (s[0] + 2, s[1])]
    assert nav.execute(path, floor, obst) is None
    obst[s[0] + 2, s[1]] = True
    assert nav.execute(path, floor, obst) == "collision"
    obst[:] = False
    floor[s[0] + 1, s[1]] = False
    assert nav.execute(path, floor, obst) == "fall"


def test_wedge_blocks_behind_and_occluded():
    floor = np.ones((nav.N, nav.N), bool)
    obst = np.zeros_like(floor)
    s = nav.START
    obst[s[0], s[1] + 10] = True  # obstacle straight ahead (yaw 0 looks +z)
    free = nav.wedge_free(obst, floor, 0.0, 65.0)
    assert free[s[0], s[1] + 5]            # visible, ahead
    assert not free[s[0], s[1] - 5]        # behind the camera: unknown
    assert not free[s[0], s[1] + 15]       # occluded by the obstacle
    assert not free[s[0] + 40, s[1] + 5]   # outside the wedge


def test_blind_radius_and_disc():
    assert abs(nav.blind_radius(1.0, 90.0, aspect=1.0) - 1.0) < 1e-9  # 45 deg half-angle: floor visible beyond 1 unit
    d = nav.disc(0.31)
    assert d[nav.START] and d[nav.START[0] + 3, nav.START[1]] and not d[nav.START[0] + 4, nav.START[1]]


def test_wedge_los_respects_r_max():
    obst = np.zeros((nav.N, nav.N), bool)
    s = nav.START
    f = nav.wedge_los(obst, 0.0, 65.0, r_max=1.0)
    assert f[s[0], s[1] + 9] and not f[s[0], s[1] + 12]
