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
        pkgs = import nixpkgs { inherit system; };
      in
      {
        packages = rec {
          volora = pkgs.python3Packages.buildPythonPackage {
            pname = "volora";
            version = "0.1.0";
            src = ./app;

            nativeBuildInputs = [ pkgs.portaudio ];

            buildInputs = [ pkgs.cowsay ];

            propagatedBuildInputs = [ pkgs.python3Packages.pyaudio ];

            meta = with pkgs.lib; {
              description = "A basic Python package that prints greeting via cowsay, with PyAudio and PortAudio dependencies";
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
            python3
            portaudio
            cowsay
            python3Packages.pyaudio
          ];
        };
      }
    );
}
