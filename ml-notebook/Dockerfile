FROM jupyter/all-spark-notebook:spark-3.3.0

MAINTAINER xiaomao23zhi <https://github.com/xiaomao23zhi>

USER root

# Install packages
RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends \
    graphviz \
    fonts-dejavu \
    gfortran \
    gcc \
    language-pack-zh-hans && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Before notebook script for sparkmagic
COPY ./sparkmagic.sh /usr/local/bin/before-notebook.d/sparkmagic.sh
RUN chmod +x /usr/local/bin/before-notebook.d/sparkmagic.sh
#COPY ./sparkmagic.sh /usr/local/bin/start-notebook.d/sparkmagic.sh
#RUN chmod +x /usr/local/bin/start-notebook.d/sparkmagic.sh
    
 # Install Julia
ARG julia_version="1.7.3"
# Julia dependencies
# install Julia packages in /opt/julia instead of ${HOME}
ENV JULIA_DEPOT_PATH=/opt/julia \
    JULIA_PKGDIR=/opt/julia \
    JULIA_VERSION="${julia_version}"

WORKDIR /tmp

# hadolint ignore=SC2046
RUN set -x && \
    julia_arch=$(uname -m) && \
    julia_short_arch="${julia_arch}" && \
    if [ "${julia_short_arch}" == "x86_64" ]; then \
      julia_short_arch="x64"; \
    fi; \
    julia_installer="julia-${JULIA_VERSION}-linux-${julia_arch}.tar.gz" && \
    julia_major_minor=$(echo "${JULIA_VERSION}" | cut -d. -f 1,2) && \
    mkdir "/opt/julia-${JULIA_VERSION}" && \
    wget -q "https://julialang-s3.julialang.org/bin/linux/${julia_short_arch}/${julia_major_minor}/${julia_installer}" && \
    tar xzf "${julia_installer}" -C "/opt/julia-${JULIA_VERSION}" --strip-components=1 && \
    rm "${julia_installer}" && \
    ln -fs /opt/julia-*/bin/julia /usr/local/bin/julia

# Show Julia where conda libraries are \
RUN mkdir /etc/julia && \
    echo "push!(Libdl.DL_LOAD_PATH, \"${CONDA_DIR}/lib\")" >> /etc/julia/juliarc.jl && \
    # Create JULIA_PKGDIR \
    mkdir "${JULIA_PKGDIR}" && \
    chown "${NB_USER}" "${JULIA_PKGDIR}" && \
    fix-permissions "${JULIA_PKGDIR}"

USER ${NB_USER}

# Add user-settings
COPY --chown=${NB_UID}:${NB_GID} user-settings/ /home/jovyan/.jupyter/lab/user-settings/

# Install from requirements.txt file
#COPY --chown=${NB_UID}:${NB_GID} requirements.txt /tmp/
#RUN pip install --no-cache-dir --requirement /tmp/requirements.txt && \

# Python packages
RUN pip install --no-cache-dir \
    jupyter-resource-usage \
    jupyterlab_execute_time \
    jupyterlab-system-monitor \
    jupyterlab-lsp \
    python-lsp-server[all] \
    jupyterlab-git \
    && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

# # Install prophet
# # RUN conda install -c conda-forge fbprophet && \
# #     conda clean -a
# RUN mamba install --quiet --yes \
#     'fbprophet' \
#     && \
#     mamba clean --all -f -y && \
#     fix-permissions "${CONDA_DIR}" && \
#     fix-permissions "/home/${NB_USER}"

# # Install elyra
# RUN pip install --upgrade elyra-pipeline-editor-extension && \
#     jupyter lab build

# R packages
RUN R -e "install.packages(c('igraph','languageserver'), dependencies=TRUE, repos='http://cran.rstudio.com/')"

# iJulia packages
RUN julia -e 'import Pkg; Pkg.update()' && \
    julia -e 'import Pkg; Pkg.add("HDF5")' && \
    julia -e 'using Pkg; Pkg.add.(["IJulia", "LanguageServer"]); pkg"precompile"' && \
    # move kernelspec out of home \
    mv "${HOME}/.local/share/jupyter/kernels/julia"* "${CONDA_DIR}/share/jupyter/kernels/" && \
    chmod -R go+rx "${CONDA_DIR}/share/jupyter" && \
    rm -rf "${HOME}/.local" && \
    fix-permissions "${CONDA_DIR}/share/jupyter"

# Install sparkmagic
RUN pip install --no-cache-dir sparkmagic && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}" && \
    jupyter-kernelspec install --user $(pip show sparkmagic | grep Location | cut -d" " -f2)/sparkmagic/kernels/sparkkernel && \
    jupyter-kernelspec install --user $(pip show sparkmagic | grep Location | cut -d" " -f2)/sparkmagic/kernels/pysparkkernel && \
    jupyter serverextension enable --py sparkmagic && \
    jupyter labextension disable ipyparallel-labextension
RUN mkdir /home/$NB_USER/.sparkmagic

COPY --chown=${NB_UID}:${NB_GID} ./config.json.template /home/$NB_USER/.sparkmagic/config.json.template
COPY --chown=${NB_UID}:${NB_GID} ./logo/spark-logo-64x64.png /home/jovyan/.local/share/jupyter/kernels/sparkkernel/logo-64x64.png
COPY --chown=${NB_UID}:${NB_GID} ./logo/pyspark-logo-64x64.png /home/jovyan/.local/share/jupyter/kernels/pysparkkernel/logo-64x64.png

# Install Dask
RUN conda create --name dask && \
    source activate dask
RUN pip install --no-cache-dir \
    dask-gateway \
    dask-ml \
    dask-labextension \
    && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}" && \
    python -m ipykernel install --user --name dask --display-name "Dask"
COPY ./logo/dask-logo-64x64.png /home/jovyan/.local/share/jupyter/kernels/dask/logo-64x64.png

# Install airflow
RUN AIRFLOW_VERSION=2.3.3 && \
    PYTHON_VERSION="$(python --version | cut -d " " -f 2 | cut -d "." -f 1-2)" && \
    CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt" && \
    pip install --no-cache-dir "apache-airflow[async,jdbc,mongo,papermill,presto,sftp]==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

# Built in kernels
COPY --chown=${NB_UID}:${NB_GID} ./kernels/ /opt/conda/share/jupyter/kernels/

# pip & conda rc
COPY --chown=${NB_UID}:${NB_GID} .condarc /home/${NB_USER}
COPY --chown=${NB_UID}:${NB_GID} .pip/ /home/${NB_USER}/.pip/

# clean up
RUN rm -rf ~/.cache/pip ~/.cache/yarn

# Dask Scheduler & Bokeh ports
EXPOSE 8787
EXPOSE 8786

WORKDIR "${HOME}"

USER $NB_UID
