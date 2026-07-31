"""Image warping service for applying transformations."""


import cv2
import numpy as np

from registration_engine.config import DEFAULT_RESAMPLING, RESAMPLING_METHODS


class ImageWarpingService:
    """Warp images using estimated transformations."""

    @staticmethod
    def get_interpolation_flag(resampling: str = DEFAULT_RESAMPLING) -> int:
        """Get OpenCV interpolation flag for resampling method.

        Args:
            resampling: Name of the resampling method.

        Returns:
            OpenCV interpolation flag.

        Raises:
            ValueError: If resampling method is not supported.
        """
        flag_map = {
            "nearest": cv2.INTER_NEAREST,
            "bilinear": cv2.INTER_LINEAR,
            "cubic": cv2.INTER_CUBIC,
        }

        name = resampling.lower()
        if name not in flag_map:
            supported = ", ".join(RESAMPLING_METHODS.keys())
            raise ValueError(
                f"Unsupported resampling: {resampling}. Supported: {supported}"
            )

        return flag_map[name]

    @staticmethod
    def warp_perspective(
        image: np.ndarray,
        matrix: np.ndarray,
        output_shape: tuple[int, int] | None = None,
        resampling: str = DEFAULT_RESAMPLING,
        fill_value: float = 0.0,
    ) -> np.ndarray:
        """Apply perspective transformation to an image.

        Args:
            image: Input image (grayscale or color).
            matrix: 3x3 transformation matrix.
            output_shape: (width, height) of output. If None, uses input size.
            resampling: Resampling method name.
            fill_value: Fill value for areas outside the image.

        Returns:
            Warped image.
        """
        if matrix is None:
            return image.copy()

        h, w = image.shape[:2]
        if output_shape is not None:
            out_w, out_h = output_shape
        else:
            out_w, out_h = w, h

        interpolation = ImageWarpingService.get_interpolation_flag(resampling)

        # Ensure matrix is 3x3
        if matrix.shape == (2, 3):
            M = np.vstack([matrix, [[0, 0, 1]]])
        else:
            M = matrix

        warped = cv2.warpPerspective(
            image,
            M,
            (out_w, out_h),
            flags=interpolation,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=fill_value,
        )

        return warped

    @staticmethod
    def warp_affine(
        image: np.ndarray,
        matrix: np.ndarray,
        output_shape: tuple[int, int] | None = None,
        resampling: str = DEFAULT_RESAMPLING,
        fill_value: float = 0.0,
    ) -> np.ndarray:
        """Apply affine transformation to an image.

        Args:
            image: Input image (grayscale or color).
            matrix: 2x3 affine transformation matrix.
            output_shape: (width, height) of output. If None, uses input size.
            resampling: Resampling method name.
            fill_value: Fill value for areas outside the image.

        Returns:
            Warped image.
        """
        if matrix is None:
            return image.copy()

        h, w = image.shape[:2]
        if output_shape is not None:
            out_w, out_h = output_shape
        else:
            out_w, out_h = w, h

        interpolation = ImageWarpingService.get_interpolation_flag(resampling)

        # Ensure matrix is 2x3
        if matrix.shape == (3, 3):
            M = matrix[:2, :]
        else:
            M = matrix

        warped = cv2.warpAffine(
            image,
            M,
            (out_w, out_h),
            flags=interpolation,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=fill_value,
        )

        return warped

    @staticmethod
    def warp_image(
        image: np.ndarray,
        matrix: np.ndarray,
        output_shape: tuple[int, int] | None = None,
        resampling: str = DEFAULT_RESAMPLING,
        fill_value: float = 0.0,
    ) -> np.ndarray:
        """Warp an image using the appropriate method based on matrix shape.

        Args:
            image: Input image.
            matrix: Transformation matrix (2x3 or 3x3).
            output_shape: (width, height) of output.
            resampling: Resampling method name.
            fill_value: Fill value for areas outside the image.

        Returns:
            Warped image.
        """
        if matrix is None:
            return image.copy()

        if matrix.shape == (3, 3):
            return ImageWarpingService.warp_perspective(
                image, matrix, output_shape, resampling, fill_value
            )
        elif matrix.shape == (2, 3):
            return ImageWarpingService.warp_affine(
                image, matrix, output_shape, resampling, fill_value
            )
        else:
            return image.copy()

    @staticmethod
    def compute_output_bounds(
        width: int,
        height: int,
        matrix: np.ndarray,
    ) -> tuple[int, int, int, int]:
        """Compute the bounding box of the warped image.

        Args:
            width: Width of the source image.
            height: Height of the source image.
            matrix: Transformation matrix.

        Returns:
            Tuple of (x_min, y_min, x_max, y_max).
        """
        corners = np.float32([
            [0, 0],
            [width, 0],
            [width, height],
            [0, height],
        ])

        if matrix.shape == (3, 3):
            corners_h = np.hstack([corners, np.ones((4, 1))])
            transformed = (matrix @ corners_h.T).T
            transformed = transformed[:, :2] / transformed[:, 2:3]
        elif matrix.shape == (2, 3):
            corners_h = np.hstack([corners, np.ones((4, 1))])
            transformed = (matrix @ corners_h.T).T
        else:
            return 0, 0, width, height

        x_min = int(np.floor(np.min(transformed[:, 0])))
        y_min = int(np.floor(np.min(transformed[:, 1])))
        x_max = int(np.ceil(np.max(transformed[:, 0])))
        y_max = int(np.ceil(np.max(transformed[:, 1])))

        return x_min, y_min, x_max, y_max

    @staticmethod
    def save_warped_image(
        image: np.ndarray,
        output_path: str,
        georef_info: dict | None = None,
    ) -> str:
        """Save a warped image to disk.

        Args:
            image: Warped image to save.
            output_path: Path to save the image.
            georef_info: Optional georeference information.

        Returns:
            Path to the saved file.
        """
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Determine file extension
        ext = os.path.splitext(output_path)[1].lower()

        if ext in (".tif", ".tiff") and georef_info is not None:
            # Save as GeoTIFF with rasterio if available
            try:
                import rasterio
                from rasterio.crs import CRS
                from rasterio.transform import from_bounds

                transform = georef_info.get("transform")
                crs = georef_info.get("crs")

                if transform is not None:
                    with rasterio.open(
                        output_path,
                        "w",
                        driver="GTiff",
                        height=image.shape[0],
                        width=image.shape[1],
                        count=1 if len(image.shape) == 2 else image.shape[2],
                        dtype=image.dtype,
                        crs=crs,
                        transform=transform,
                    ) as dst:
                        if len(image.shape) == 2:
                            dst.write(image, 1)
                        else:
                            for i in range(image.shape[2]):
                                dst.write(image[:, :, i], i + 1)
                    return output_path
            except ImportError:
                pass

        # Fallback: save with OpenCV
        cv2.imwrite(output_path, image)
        return output_path
