{
  description = "peepee poopoo";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [
            (final: prev: {
              pycodec2 = prev.python3Packages.buildPythonPackage {
                pname = "pycodec2";
                version = "4.1.0";

                src = prev.fetchPypi {
                  pname = "pycodec2";
                  version = "4.1.0";
                  sha256 = "46a491f4c8e2328cb633b40ef6dccbd2ea08da51f6b76e795c4d7a439f8d355b";
                };

                buildInputs = with pkgs; [
                  codec2
                ];

                propagatedBuildInputs = with prev.python3Packages; [
                  cython
                  numpy
                ];

                meta = with prev.lib; {
                  description = "Python binding for codec2";
                  license = prev.lib.licenses.mit;
                  platforms = prev.lib.platforms.all;
                };

              };
            })
          ];
        };
      in
      {
        packages = rec {
          volora = pkgs.python3Packages.buildPythonPackage {
            pname = "volora";
            version = "0.1.0";
            src = ./app;

            nativeBuildInputs = with pkgs; [
              codec2
              portaudio
              sox
            ];

            buildInputs = with pkgs; [ cowsay ];

            propagatedBuildInputs = with pkgs; [
              pycodec2
              python3Packages.pyaudio
              python3Packages.soxr
            ];

            meta = with pkgs.lib; {
              description = "Volora";
              license = licenses.mit;
              platforms = platforms.all;
            };

            postFixup = ''
              wrapProgram $out/bin/volora --prefix PATH : ${pkgs.cowsay}/bin
            '';
          };

          default = volora;
        };

        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [
            cowsay
            portaudio
            sox
            (python3.withPackages (
              ps: with ps; [
                ipykernel
                pyaudio
                soxr
                pycodec2
              ]
            ))
          ];

          shellHook = ''
            VENV_DIR=".venv"
            echo "Checking for virtual environment in $${VENV_DIR}..."
            if [ ! -d "$VENV_DIR" ]; then
              echo "No virtual environment found. Creating one with --system-site-packages..."
              python -m venv --system-site-packages "$VENV_DIR"
            fi
            echo "Activating virtual environment..."
            . "$VENV_DIR/bin/activate"
          '';
        };

      }
    );
}
