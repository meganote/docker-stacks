# Copyright (c) NONE
ARG BASE_IMAGE=jupyter/all-spark-notebook:spark-3.3.2
ARG JULIA_VERSION=1.7.3
ARG AIRFLOW_VERSION=2.4.3
FROM $BASE_IMAGE

LABEL maintainer="Meganote Project <https://github.com/meganote>"

# Fix: https://github.com/hadolint/hadolint/wiki/DL4006
# Fix: https://github.com/koalaman/shellcheck/wiki/SC3014
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

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

# Julia dependencies
# install Julia packages in /opt/julia instead of ${HOME}
ENV JULIA_HOME=/opt/julia \
    JULIA_VERSION="${JULIA_VERSION}"

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
    mkdir "${JULIA_HOME}" && \
    wget -q "https://julialang-s3.julialang.org/bin/linux/${julia_short_arch}/${julia_major_minor}/${julia_installer}" && \
    tar xzf "${julia_installer}" -C "${JULIA_HOME}" --strip-components=1 && \
    rm "${julia_installer}" && \
    ln -fs /opt/julia/bin/julia /usr/local/bin/julia

# Show Julia where conda libraries are \
RUN mkdir /etc/julia && \
    echo "push!(Libdl.DL_LOAD_PATH, \"${CONDA_DIR}/lib\")" >> /etc/julia/juliarc.jl && \
    chown "${NB_USER}" "${JULIA_HOME}" && \
    fix-permissions "${JULIA_HOME}"

USER ${NB_UID}

# Install from requirements.txt file
#COPY --chown=${NB_UID}:${NB_GID} requirements.txt /tmp/
#RUN pip install --no-cache-dir --requirement /tmp/requirements.txt && \

# Python packages
RUN mamba install --quiet --yes \
    jupyter-resource-usage \
    jupyterlab_execute_time \
    jupyterlab-system-monitor \
    jupyterlab-lsp \
    python-lsp-server[all] \
    jupyterlab-git \
    && \
    mamba clean --all -f -y && \
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
    jupyter-kernelspec install --user $(pip show sparkmagic | grep Location | cut -d" " -f2)/sparkmagic/kernels/sparkrkernel && \
    mv "${HOME}/.local/share/jupyter/kernels/sparkkernel"* "${CONDA_DIR}/share/jupyter/kernels/" && \
    mv "${HOME}/.local/share/jupyter/kernels/pysparkkernel"* "${CONDA_DIR}/share/jupyter/kernels/" && \
    mv "${HOME}/.local/share/jupyter/kernels/sparkrkernel"* "${CONDA_DIR}/share/jupyter/kernels/" && \
    jupyter serverextension enable --py sparkmagic && \
    jupyter labextension disable ipyparallel-labextension && \
    fix-permissions "${CONDA_DIR}/share/jupyter"
RUN mkdir /home/$NB_USER/.sparkmagic

COPY --chown=${NB_UID}:${NB_GID} ./config.json.template /home/$NB_USER/.sparkmagic/config.json.template
#COPY --chown=${NB_UID}:${NB_GID} ./logo/spark-logo-64x64.png /home/jovyan/.local/share/jupyter/kernels/sparkkernel/logo-64x64.png
#COPY --chown=${NB_UID}:${NB_GID} ./logo/pyspark-logo-64x64.png /home/jovyan/.local/share/jupyter/kernels/pysparkkernel/logo-64x64.png
#COPY --chown=${NB_UID}:${NB_GID} ./logo/sparkr-logo-64x64.png /home/jovyan/.local/share/jupyter/kernels/sparkrkernel/logo-64x64.png
COPY --chown=${NB_UID}:${NB_GID} ./logo/spark-logo-64x64.png ${CONDA_DIR}/share/jupyter/kernels/sparkkernel/logo-64x64.png
COPY --chown=${NB_UID}:${NB_GID} ./logo/pyspark-logo-64x64.png ${CONDA_DIR}/share/jupyter/kernels/pysparkkernel/logo-64x64.png
COPY --chown=${NB_UID}:${NB_GID} ./logo/sparkr-logo-64x64.png ${CONDA_DIR}/share/jupyter/kernels/sparkrkernel/logo-64x64.png

# Install Dask
RUN conda create --name dask && \
    source activate dask
RUN mamba install --quiet --yes \
    dask-gateway \
    dask-ml \
    dask-labextension \
    && \
    mamba clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}" && \
    python -m ipykernel install --user --name dask --display-name "Dask" && \
    mv "${HOME}/.local/share/jupyter/kernels/dask"* "${CONDA_DIR}/share/jupyter/kernels/" && \
    fix-permissions "${CONDA_DIR}/share/jupyter"
COPY --chown=${NB_UID}:${NB_GID} ./logo/dask-logo-svg.svg ${CONDA_DIR}/share/jupyter/kernels/dask/logo-svg.svg

# Install airflow
RUN AIRFLOW_VERSION=${AIRFLOW_VERSION} && \
    PYTHON_VERSION="$(python --version | cut -d " " -f 2 | cut -d "." -f 1-2)" && \
    CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt" && \
    pip install --no-cache-dir "apache-airflow[async,jdbc,mongo,papermill,presto,sftp]==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}" && \
    fix-permissions "${CONDA_DIR}/share/jupyter"

## Built in kernels
#COPY --chown=${NB_UID}:${NB_GID} ./kernels/ /opt/conda/share/jupyter/kernels/

# pip & conda rc
COPY --chown=${NB_UID}:${NB_GID} .condarc /home/${NB_USER}
COPY --chown=${NB_UID}:${NB_GID} .pip/ /home/${NB_USER}/.pip/

# Add user-settings
COPY --chown=${NB_UID}:${NB_GID} user-settings/ /home/jovyan/.jupyter/lab/user-settings/

# clean up
RUN rm -rf ~/.cache/pip ~/.cache/yarn

# Dask Scheduler & Bokeh ports
EXPOSE 8787
EXPOSE 8786

WORKDIR "${HOME}"
