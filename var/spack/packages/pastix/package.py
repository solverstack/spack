from spack import *
import os
import platform

class Pastix(Package):
    """a high performance parallel solver for very large sparse linear systems based on direct methods"""
    homepage = "http://pastix.gforge.inria.fr/files/README-txt.html"

    version('5.2.2.20', '67a1a054fad0f4c5bcbd7abe855667a8',
            url='https://gforge.inria.fr/frs/download.php/file/34392/pastix_5.2.2.20.tar.bz2')
    version('5.2.2.22', '85127ecdfaeed39e850c996b78573d94',
            url='https://gforge.inria.fr/frs/download.php/file/35070/pastix_5.2.2.22.tar.bz2')
    version('master', git='https://scm.gforge.inria.fr/anonscm/git/ricar/ricar.git', branch='master')
    version('develop', git='https://scm.gforge.inria.fr/anonscm/git/ricar/ricar.git', branch='develop')

    variant('mpi', default=False, description='Enable MPI')
    variant('cuda', default=False, description='Enable CUDA kernels. Caution: only available if StarPU variant is enabled')
    variant('metis', default=False, description='Enable Metis')
    variant('starpu', default=False, description='Enable StarPU')
    variant('shared', default=True, description='Build Pastix as a shared library')
    variant('examples', default=False, description='Enable compilation and installation of example executables')

    depends_on("hwloc")
    depends_on("mpi", when='+mpi')
    depends_on("blas")
    depends_on("scotch")
    depends_on("scotch+mpi", when='+examples+mpi')
    depends_on("metis@4.0.3", when='+metis')
    depends_on("starpu@1.1.0:1.1.5", when='+starpu')

    def setup(self):

        force_symlink('config/LINUX-GNU.in', 'config.in')

        mf = FileFilter('config.in')
        spec = self.spec

        mf.filter('CCPROG      = gcc -Wall', 'CCPROG      = cc -Wall\nCXXPROG     = c++ -Wall')
        mf.filter('CFPROG      = gfortran', 'CFPROG      = f77')
        mf.filter('CF90PROG    = gfortran', 'CF90PROG    = f90')

        mf.filter('^# ROOT          =.*', 'ROOT          = %s' % spec.prefix)
        mf.filter('^# INCLUDEDIR    =.*', 'INCLUDEDIR    = ${ROOT}/include')
        mf.filter('^# LIBDIR        =.*', 'LIBDIR        = ${ROOT}/lib')
        mf.filter('^# BINDIR        =.*', 'BINDIR        = ${ROOT}/bin')
        mf.filter('^# PYTHON_PREFIX =.*', 'PYTHON_PREFIX = ${ROOT}')

        if spec.satisfies('+shared'):
            mf.filter('#SHARED=1', 'SHARED=1')
            mf.filter('#SOEXT=\.so', 'SOEXT=.so')
            mf.filter('#SHARED_FLAGS =  -shared -Wl,-soname,__SO_NAME__', 'SHARED_FLAGS =  -shared')
            if platform.system() == 'Darwin':
                mf.filter('\.so', '.dylib')
                mf.filter('-shared -Wl,-soname,__SO_NAME__', '-shared')
            mf.filter('#CCFDEB       := \$\{CCFDEB\} -fPIC', 'CCFDEB       := ${CCFDEB} -fPIC')
            mf.filter('#CCFOPT       := \$\{CCFOPT\} -fPIC', 'CCFOPT       := ${CCFOPT} -fPIC')
            mf.filter('#CFPROG       := \$\{CFPROG\} -fPIC', 'CFPROG       := ${CFPROG} -fPIC')

        if not spec.satisfies('+mpi'):
            mf.filter('^#VERSIONMPI  = _nompi', 'VERSIONMPI  = _nompi')
            mf.filter('^#CCTYPES    := \$\(CCTYPES\) -DFORCE_NOMPI', 'CCTYPES    := $(CCTYPES) -DFORCE_NOMPI')
            mf.filter('^#MPCCPROG    = \$\(CCPROG\)', 'MPCCPROG    = $(CCPROG)\nMPCXXPROG   = $(CXXPROG)')
            mf.filter('^#MCFPROG     = \$\(CFPROG\)', 'MCFPROG     = $(CFPROG)')
        else:
            mf.filter('mpic\+\+', 'mpicxx') # mpic++ does not exist with hpmpi

        if spec.satisfies('+starpu'):
            starpu = spec['starpu'].prefix
            if '^starpu+mpi' in spec:
                mf.filter('^#CCPASTIX   := \$\(CCPASTIX\) `pkg-config libstarpu --cflags` -DWITH_STARPU', 'CCPASTIX   := $(CCPASTIX) `pkg-config libstarpumpi --cflags` -DWITH_STARPU')
                mf.filter('^#EXTRALIB   := \$\(EXTRALIB\) `pkg-config libstarpu --libs`', 'EXTRALIB   := $(EXTRALIB) `pkg-config libstarpumpi --libs`')
            else:
                mf.filter('^#CCPASTIX   := \$\(CCPASTIX\) `pkg-config libstarpu --cflags` -DWITH_STARPU', 'CCPASTIX   := $(CCPASTIX) `pkg-config libstarpu --cflags` -DWITH_STARPU')
                mf.filter('^#EXTRALIB   := \$\(EXTRALIB\) `pkg-config libstarpu --libs`', 'EXTRALIB   := $(EXTRALIB) `pkg-config libstarpu --libs`')

        if spec.satisfies('+metis'):
            metis = spec['metis'].prefix
            metis_libs = " ".join(metislibname)
            mf.filter('^#VERSIONORD  = _metis', 'VERSIONORD  = _metis')
            mf.filter('^#METIS_HOME  =.*', 'METIS_HOME  = %s' % metis)
            mf.filter('^#CCPASTIX   := \$\(CCPASTIX\) -DMETIS -I\$\(METIS_HOME\)/Lib', 'CCPASTIX   := $(CCPASTIX) -DMETIS -I$(METIS_HOME)/Lib')
            mf.filter('^#EXTRALIB   := \$\(EXTRALIB\) -L\$\(METIS_HOME\) -lmetis', 'EXTRALIB   := $(EXTRALIB) -L$(METIS_HOME) -lmetis')

        scotch = spec['scotch'].prefix
        scotch_libs = " ".join(scotchlibname)
        mf.filter('^SCOTCH_HOME \?= \$\{HOME\}/scotch_5.1/', 'SCOTCH_HOME = %s' % scotch)
        if not spec.satisfies('^scotch+mpi'):
            mf.filter('#CCPASTIX   := \$\(CCPASTIX\) -I\$\(SCOTCH_INC\) -DWITH_SCOTCH',
                      'CCPASTIX   := $(CCPASTIX) -I$(SCOTCH_INC) -DWITH_SCOTCH')
            mf.filter('#EXTRALIB   := \$\(EXTRALIB\) -L\$\(SCOTCH_LIB\) -lscotch -lscotcherrexit',
                      'EXTRALIB   := $(EXTRALIB) -L$(SCOTCH_LIB) -lscotch -lscotcherrexit -lz -lm -lpthread')
            mf.filter('CCPASTIX   := \$\(CCPASTIX\) -I\$\(SCOTCH_INC\) -DDISTRIBUTED -DWITH_SCOTCH',
                      '#CCPASTIX   := $(CCPASTIX) -I$(SCOTCH_INC) -DDISTRIBUTED -DWITH_SCOTCH')
            mf.filter('EXTRALIB   := \$\(EXTRALIB\) -L\$\(SCOTCH_LIB\) -lptscotch -lscotch -lptscotcherrexit',
                      '#EXTRALIB   := $(EXTRALIB) -L$(SCOTCH_LIB) -lptscotch -lscotch -lptscotcherrexit')
        else:
            mf.filter('EXTRALIB   := \$\(EXTRALIB\) -L\$\(SCOTCH_LIB\) -lptscotch -lscotch -lptscotcherrexit',
                      'EXTRALIB   := $(EXTRALIB) -L$(SCOTCH_LIB) -lptscotch -lscotch -lptscotcherrexit -lz -lm -lpthread')

        hwloc = spec['hwloc'].prefix
        mf.filter('^HWLOC_HOME \?= /opt/hwloc/', 'HWLOC_HOME = %s' % hwloc)

        blas = spec['blas'].prefix
        blas_libs = " ".join(blaslibname)
        if '^netlib-blas' in spec:
            mf.filter('BLASLIB  = -lblas', 'BLASLIB  = -L%s -lblas -lm' % blas.lib)
        elif '^mkl-blas' in spec:
            mf.filter('BLASLIB  = -lblas', 'BLASLIB  = %s' % blas_libs)

        mf.filter('LDFLAGS  = $(EXTRALIB) $(BLASLIB)', 'LDFLAGS  = $(BLASLIB) $(EXTRALIB)')

        if platform.system() == 'Darwin':
            mf.filter('-lrt', '')
            mf.filter('i686_pc_linux', 'i686_mac')

    def install(self, spec, prefix):

        with working_dir('src'):

            self.setup()
            make()
            if spec.satisfies('+examples'):
                make('examples')
            make("install")
            # examples are not installed by default
            if spec.satisfies('+examples'):
                install_tree('example/bin', '%s/lib/pastix/examples' % prefix)
