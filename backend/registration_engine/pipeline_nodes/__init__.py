"""Registration pipeline nodes for the GARUDA pipeline engine."""

import json
import os

import cv2
import numpy as np

from pipeline_engine.nodes import BaseNode, register_node
from registration_engine.config import (
    DEFAULT_FEATURE_DETECTOR,
    DEFAULT_FEATURE_MATCHER,
    DEFAULT_RESAMPLING,
    DEFAULT_TRANSFORM_TYPE,
)
from registration_engine.services.feature_detection import FeatureDetectionService
from registration_engine.services.feature_matching import FeatureMatchingService
from registration_engine.services.image_warping import ImageWarpingService
from registration_engine.services.quality_metrics import QualityMetricsService
from registration_engine.services.transform_estimation import TransformEstimationService


@register_node(
    node_id="registration_detect_features",
    name="Feature Detection",
    description="Detect image features using ORB, AKAZE, BRISK, or SIFT",
    category="registration",
    inputs=["image_path"],
    outputs=["image", "keypoints", "descriptors", "feature_count"],
)
class RegistrationDetectFeaturesNode(BaseNode):
    """Detect features in a single image."""

    def execute(self, inputs, config, context):
        image_path = inputs.get("image_path")
        if not image_path or not os.path.exists(image_path):
            raise ValueError(f"Image not found: {image_path}")

        detector = config.get("feature_detector", DEFAULT_FEATURE_DETECTOR)
        max_features = config.get("max_features")

        kwargs = {}
        if detector == "orb" and max_features:
            kwargs["max_features"] = max_features

        image, keypoints, descriptors = (
            FeatureDetectionService.detect_features_from_file(
                image_path, detector, **kwargs
            )
        )

        return {
            "image": image,
            "keypoints": keypoints,
            "descriptors": descriptors,
            "feature_count": FeatureDetectionService.get_keypoint_count(descriptors),
        }


@register_node(
    node_id="registration_match_features",
    name="Feature Matching",
    description="Match features between reference and target images",
    category="registration",
    inputs=["ref_descriptors", "tgt_descriptors", "ref_keypoints", "tgt_keypoints"],
    outputs=["matches", "points_ref", "points_tgt", "match_count"],
)
class RegistrationMatchFeaturesNode(BaseNode):
    """Match features between two images."""

    def execute(self, inputs, config, context):
        ref_desc = inputs.get("ref_descriptors")
        tgt_desc = inputs.get("tgt_descriptors")
        ref_kp = inputs.get("ref_keypoints")
        tgt_kp = inputs.get("tgt_keypoints")

        if ref_desc is None or tgt_desc is None:
            raise ValueError("Descriptor inputs are required")

        matcher = config.get("feature_matcher", DEFAULT_FEATURE_MATCHER)
        detector = config.get("feature_detector", DEFAULT_FEATURE_DETECTOR)

        matches = FeatureMatchingService.match_descriptors(
            ref_desc, tgt_desc, matcher, detector
        )

        points_ref, points_tgt = FeatureMatchingService.match_to_points(
            ref_kp, tgt_kp, matches
        )

        return {
            "matches": matches,
            "points_ref": points_ref,
            "points_tgt": points_tgt,
            "match_count": len(matches),
        }


@register_node(
    node_id="registration_estimate_transform",
    name="Transform Estimation",
    description="Estimate geometric transformation between matched point sets",
    category="registration",
    inputs=["points_ref", "points_tgt"],
    outputs=["transform_matrix", "inlier_mask", "inlier_ratio", "rmse"],
)
class RegistrationEstimateTransformNode(BaseNode):
    """Estimate a geometric transformation from matched points."""

    def execute(self, inputs, config, context):
        points_ref = inputs.get("points_ref")
        points_tgt = inputs.get("points_tgt")

        if points_ref is None or points_tgt is None:
            raise ValueError("Point inputs are required")

        transform_type = config.get("transform_type", DEFAULT_TRANSFORM_TYPE)
        ransac_threshold = config.get("ransac_threshold", 5.0)

        matrix, inlier_mask, inlier_ratio = (
            TransformEstimationService.estimate_transform(
                points_ref, points_tgt, transform_type, ransac_threshold
            )
        )

        if matrix is None:
            raise ValueError("Failed to estimate transformation")

        rmse = TransformEstimationService.compute_rmse(
            points_ref, points_tgt, matrix, inlier_mask
        )

        return {
            "transform_matrix": matrix,
            "inlier_mask": inlier_mask,
            "inlier_ratio": inlier_ratio,
            "rmse": rmse,
        }


@register_node(
    node_id="registration_warp_image",
    name="Image Warping",
    description="Apply geometric transformation to align the target image",
    category="registration",
    inputs=["target_image", "transform_matrix"],
    outputs=["warped_image", "output_path"],
)
class RegistrationWarpImageNode(BaseNode):
    """Warp an image using an estimated transformation."""

    def execute(self, inputs, config, context):
        target_image = inputs.get("target_image")
        matrix = inputs.get("transform_matrix")

        if target_image is None or matrix is None:
            raise ValueError("Target image and transform matrix are required")

        resampling = config.get("resampling", DEFAULT_RESAMPLING)
        output_path = config.get("output_path", "registered_output.tif")

        warped = ImageWarpingService.warp_image(
            target_image, matrix, resampling=resampling
        )

        ImageWarpingService.save_warped_image(warped, output_path)

        return {
            "warped_image": warped,
            "output_path": output_path,
        }


@register_node(
    node_id="registration_compute_quality",
    name="Quality Assessment",
    description="Compute registration quality metrics and grade",
    category="registration",
    inputs=[
        "points_ref", "points_tgt", "transform_matrix",
        "inlier_mask", "inlier_ratio", "rmse",
    ],
    outputs=["quality", "overall_score", "quality_grade", "is_acceptable"],
)
class RegistrationComputeQualityNode(BaseNode):
    """Assess the quality of a registration."""

    def execute(self, inputs, config, context):
        points_ref = inputs.get("points_ref")
        points_tgt = inputs.get("points_tgt")
        matrix = inputs.get("transform_matrix")
        inlier_mask = inputs.get("inlier_mask")
        inlier_ratio = inputs.get("inlier_ratio", 0.0)
        rmse = inputs.get("rmse", float("inf"))

        residuals = None
        inlier_count = 0
        if points_ref is not None and points_tgt is not None and matrix is not None:
            residuals = TransformEstimationService.compute_residuals(
                points_ref, points_tgt, matrix
            )
            if inlier_mask is not None:
                inlier_count = int(np.sum(inlier_mask))
                inlier_residuals = residuals[inlier_mask] if inlier_mask.any() else residuals
            else:
                inlier_count = len(residuals)
                inlier_residuals = residuals

        quality = QualityMetricsService.evaluate_registration_quality(
            rmse=rmse,
            inlier_ratio=inlier_ratio,
            matched_points=len(points_ref) if points_ref is not None else 0,
            inlier_count=inlier_count,
            transform_matrix=matrix,
            residuals=inlier_residuals if residuals is not None else None,
        )

        return {
            "quality": quality,
            "overall_score": quality["overall_score"],
            "quality_grade": quality["quality_grade"],
            "is_acceptable": quality["is_acceptable"],
        }


@register_node(
    node_id="registration_full",
    name="Full Registration",
    description="Execute the complete automatic registration pipeline",
    category="registration",
    inputs=["reference_path", "target_path"],
    outputs=["output_path", "quality", "transform_matrix", "rmse"],
)
class RegistrationFullNode(BaseNode):
    """Execute a complete automatic registration as a single node."""

    def execute(self, inputs, config, context):
        reference_path = inputs.get("reference_path")
        target_path = inputs.get("target_path")

        if not reference_path or not os.path.exists(reference_path):
            raise ValueError(f"Reference image not found: {reference_path}")
        if not target_path or not os.path.exists(target_path):
            raise ValueError(f"Target image not found: {target_path}")

        detector = config.get("feature_detector", DEFAULT_FEATURE_DETECTOR)
        matcher = config.get("feature_matcher", DEFAULT_FEATURE_MATCHER)
        transform_type = config.get("transform_type", DEFAULT_TRANSFORM_TYPE)
        resampling = config.get("resampling", DEFAULT_RESAMPLING)
        output_path = config.get(
            "output_path",
            os.path.join(
                os.path.dirname(target_path),
                f"registered_{os.path.basename(target_path)}",
            ),
        )

        # Detect
        ref_img, ref_kp, ref_desc = (
            FeatureDetectionService.detect_features_from_file(
                reference_path, detector
            )
        )
        tgt_img, tgt_kp, tgt_desc = (
            FeatureDetectionService.detect_features_from_file(
                target_path, detector
            )
        )

        # Match
        matches = FeatureMatchingService.match_descriptors(
            ref_desc, tgt_desc, matcher, detector
        )
        points_ref, points_tgt = FeatureMatchingService.match_to_points(
            ref_kp, tgt_kp, matches
        )

        if len(matches) < 4:
            raise ValueError(f"Insufficient matches: {len(matches)}")

        # Estimate
        matrix, inlier_mask, inlier_ratio = (
            TransformEstimationService.estimate_transform(
                points_ref, points_tgt, transform_type
            )
        )

        if matrix is None:
            raise ValueError("Failed to estimate transformation")

        # Quality
        inlier_count = int(np.sum(inlier_mask))
        residuals = TransformEstimationService.compute_residuals(
            points_ref, points_tgt, matrix
        )
        inlier_residuals = residuals[inlier_mask] if inlier_mask.any() else residuals
        rmse = TransformEstimationService.compute_rmse(
            points_ref, points_tgt, matrix, inlier_mask
        )

        quality = QualityMetricsService.evaluate_registration_quality(
            rmse=rmse,
            inlier_ratio=inlier_ratio,
            matched_points=len(matches),
            inlier_count=inlier_count,
            transform_matrix=matrix,
            residuals=inlier_residuals,
        )

        # Warp
        warped = ImageWarpingService.warp_image(
            tgt_img, matrix, resampling=resampling
        )
        ImageWarpingService.save_warped_image(warped, output_path)

        return {
            "output_path": output_path,
            "quality": quality,
            "transform_matrix": matrix,
            "rmse": rmse,
        }
