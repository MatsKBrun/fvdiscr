import numpy as np

from core.constit import fourth_order_tensor
from core.bc import bc
from fvdiscr import mpsa
from fvdiscr import fvutils
from fvdiscr.tests import setup_grids


def setup_stiffness(g, mu=1, l=1):
    mu = np.ones(g.num_cells) * mu
    l = np.ones(g.num_cells) * l
    return fourth_order_tensor.FourthOrderTensor(g.dim, mu, l)


def test_uniform_strain():
    g_list = setup_grids.setup_2d()

    for g in g_list:
        bound_faces = np.argwhere(np.abs(g.cell_faces)
                                  .sum(axis=1).A.ravel('F') == 1)
        bound = bc.BoundaryCondition(g, bound_faces.ravel('F'),
                                     ['dir'] * bound_faces.size)
        mu = 1
        l = 1
        constit = setup_stiffness(g, mu, l)

        # Python inverter is most efficient for small problems
        stress, bound_stress = mpsa.mpsa(g, constit, bound, inverter='python')

        div = fvutils.vector_divergence(g)
        a = div * stress

        xc = g.cell_centers
        xf = g.face_centers

        gx = np.random.rand(1)
        gy = np.random.rand(1)

        dc_x = np.sum(xc * gx, axis=0)
        dc_y = np.sum(xc * gy, axis=0)
        df_x = np.sum(xf * gx, axis=0)
        df_y = np.sum(xf * gy, axis=0)

        d_bound = np.zeros((g.dim, g.num_faces))
        d_bound[0, bound.is_dir] = df_x[bound.is_dir]
        d_bound[1, bound.is_dir] = df_y[bound.is_dir]

        rhs = div * bound_stress * d_bound.ravel('F')

        d = np.linalg.solve(a.todense(), rhs)

        traction = stress * d - bound_stress * d_bound.ravel('F')

        s_xx = (2*mu+l) * gx + l * gy
        s_xy = mu * (gx + gy)
        s_yx = mu * (gx + gy)
        s_yy = (2*mu+l) * gy + l * gx

        n = g.face_normals
        traction_ex_x = s_xx * n[0] + s_xy * n[1]
        traction_ex_y = s_yx * n[0] + s_yy * n[1]

        assert np.max(np.abs(d[::2] - dc_x)) < 1e-8
        assert np.max(np.abs(d[1::2] - dc_y)) < 1e-8
        assert np.max(np.abs(traction[::2]-traction_ex_x)) < 1e-8
        assert np.max(np.abs(traction[1::2]-traction_ex_y)) < 1e-8


def test_uniform_displacement():

    g_list = setup_grids.setup_2d()

    for g in g_list:
        bound_faces = np.argwhere(np.abs(g.cell_faces)
                                  .sum(axis=1).A.ravel('F')==1)
        bound = bc.BoundaryCondition(g, bound_faces.ravel(1),
                                     ['dir'] * bound_faces.size)
        constit = setup_stiffness(g)

        # Python inverter is most efficient for small problems
        stress, bound_stress = mpsa.mpsa(g, constit, bound, inverter='python')

        div = fvutils.vector_divergence(g)
        a = div * stress

        d_x = np.random.rand(1)
        d_y = np.random.rand(1)
        d_bound = np.zeros((g.dim, g.num_faces))
        d_bound[0, bound.is_dir] = d_x
        d_bound[1, bound.is_dir] = d_y

        rhs = div * bound_stress * d_bound.ravel('F')

        d = np.linalg.solve(a.todense(), rhs)

        traction = stress * d - bound_stress * d_bound.ravel('F')

        assert np.max(np.abs(d[::2] - d_x)) < 1e-8
        assert np.max(np.abs(d[1::2] - d_y)) < 1e-8
        assert np.max(np.abs(traction)) < 1e-8

if __name__ == '__main__':
    test_uniform_displacement()
    test_uniform_strain()
