from predict import load_model ,generate_caption
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from rclpy.node import Node
from pathlib import Path
import rclpy

class FastVLMNode(Node):
    def __init__(self):
        super().__init__('fastvlm_caption_node')
        self.get_logger().info('FastVLM Caption Node Starting...')
        
        self.caption_pub = self.create_publisher(String, '/visual_memory/caption', 10)
        self.bridge = CvBridge()
        
        self.current_image = None

        # Need to add this as parameter
        self.caption_interval = 8.0   # Seconds between captions
        
        # Need to add this as parameter
        model_path = Path("~/Desktop/checkpoints/llava-fastvithd_1.5b_stage3").expanduser()
        load_model(model_path)

        # Subscribers
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        
        # Timer for periodic captioning (handles rate limiting)
        self.timer = self.create_timer(self.caption_interval, self.caption_timer_callback)
        
    def image_callback(self, msg):
        """Store latest image from Gazebo/camera"""
        try:
            self.current_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
        except Exception as e:
            self.get_logger().warn(f'Image conversion failed: {e}')
    
    def caption_timer_callback(self):
        """Generate caption every X seconds if new image available"""
        if self.current_image is None: return 

        caption = self.generate_caption(self.current_image)
        if caption:
            msg = String()
            msg.data = caption
            self.caption_pub.publish(msg)
            self.get_logger().info(f'caption generated: {caption}')
    
    def generate_caption(self, cv_image):
        """Generate caption using FastVLM"""
        try:
            return generate_caption(cv_image=cv_image)
            
        except Exception as e:
            self.get_logger().error(f'Caption generation failed: {e}')
            return None

def main(args=None):
    rclpy.init(args=args)
    node = FastVLMNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()